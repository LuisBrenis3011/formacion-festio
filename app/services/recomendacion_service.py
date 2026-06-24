"""
Motor de Recomendación Jerárquico v3.
Consciente del inventario. Comportamiento de vendedor real.
Categorías y temáticas dinámicas desde la base de datos.
"""
import re
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Set, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.domain.catalogo.models import Categoria, DetallePaquete, Paquete, ServicioProducto, Tematica
from app.domain.disponibilidad.models import OcupacionServicioProducto
from app.domain.common.enums import EstadoBasico, EstadoVerificacion
from app.domain.usuarios.models import Proveedor
from app.domain.chat.schemas import (
    ItemRecomendado, PaqueteRecomendado, ProveedorRecomendado,
    RecomendacionRequest, RecomendacionResponse,
)
from app.domain.reservas.schemas import PreReservaCreate, PreReservaItemCreate

# ═══════════════════════════════════════════════════════════════════════════════
# HEURÍSTICAS DE NEGOCIO (no son datos de catálogo)
# ═══════════════════════════════════════════════════════════════════════════════
CROSS_SELL: Dict[str, Set[str]] = {
    "shows infantiles":    {"caritas pintadas", "burbujas", "muneco", "personaje"},
    "personal y musica":   {"luces", "zancos", "arlequin"},
    "hora loca":           {"luces", "zancos", "arlequin", "bailarin"},
    "mobiliario y decoracion": {"silla", "mesa", "toldo", "decoracion"},
}
# Palabras de servicio aislado (Regla 3: detectar CASO A)
SERVICIO_AISLADO: Dict[str, str] = {
    "dj": "Personal y Música", "animadora": "Shows Infantiles", "animador": "Shows Infantiles",
    "bailarina": "Hora Loca", "bailarin": "Hora Loca",
}
STOPWORDS: Set[str] = {
    "show", "fiesta", "evento", "reunion", "celebracion", "paquete",
    "servicio", "quiero", "necesito", "busco", "algo", "para", "con",
    "del", "los", "las", "una", "unos", "unas", "que", "como", "mas",
}
# Palabras que indican experiencia completa (no servicio aislado)
PALABRAS_EXPERIENCIA: Set[str] = {
    "show", "paquete", "evento", "fiesta", "infantil", "completo",
}


def _cargar_contexto_db(db: Session) -> Tuple[List[Categoria], List[Tematica], Set[str]]:
    """Carga categorías, temáticas y nombres normalizados desde la BD."""
    categorias_db = db.query(Categoria).all()
    tematicas_db = db.query(Tematica).all()
    nombres_tematicas = {_norm(t.nombre) for t in tematicas_db}
    return categorias_db, tematicas_db, nombres_tematicas


def recomendar_evento(datos: RecomendacionRequest, db: Session) -> RecomendacionResponse:
    texto = _norm(datos.mensaje)

    # ── Cargar contexto dinámico desde la BD ──────────────────────────────
    categorias_db, tematicas_db, nombres_tematicas = _cargar_contexto_db(db)

    # ── Fase 1: Detección jerárquica — Gemini provee, texto como apoyo ───
    tipo_evento = datos.tipo_evento
    tematica = datos.tematica_detectada
    servicios_pedidos = set(datos.servicios_extra_detectados) if datos.servicios_extra_detectados else set()
    cantidades = datos.cantidades_servicios or _detectar_cantidades(texto, datos.aforo_estimado)
    busca_barato = _detecta_bajo_presupuesto(texto)

    # Inferencia jerárquica: si hay temática pero no tipo, inferir Shows Infantiles
    if tipo_evento is None and tematica:
        tipo_evento = "Shows Infantiles"

    es_ambiguo = tipo_evento is None and tematica is None and not servicios_pedidos

    # ── Regla 3: ¿Servicio aislado o experiencia completa? ────────────────
    modo_servicio = _es_servicio_aislado(texto, tipo_evento)

    datos_faltantes = _datos_faltantes_prebloqueo(datos)

    # ── Fase 2: Consultar proveedores verificados ─────────────────────────
    query = (
        db.query(Proveedor)
        .options(
            joinedload(Proveedor.paquetes).joinedload(Paquete.detalles)
                .joinedload(DetallePaquete.servicio_producto),
            joinedload(Proveedor.paquetes).joinedload(Paquete.categoria),
            joinedload(Proveedor.servicios_productos),
        )
        .filter(Proveedor.estado_verificacion == EstadoVerificacion.VERIFICADO)
    )
    if datos.distrito:
        query = query.filter(Proveedor.distrito.ilike(f"%{datos.distrito}%"))

    # ── Filtros opcionales del usuario ────────────────────────────────────
    if datos.filtro_proveedor_ids:
        query = query.filter(Proveedor.id.in_(datos.filtro_proveedor_ids))

    principales: List[ProveedorRecomendado] = []
    secundarios: List[ProveedorRecomendado] = []
    scores: Dict[int, int] = {}  # proveedor_id -> score (Regla 10)

    for prov in query.all():
        paq_activos = [p for p in prov.paquetes if p.estado == EstadoBasico.ACTIVO]
        # ── Filtro de categoría sobre paquetes ────────────────────────────
        if datos.filtro_categoria_ids:
            paq_activos = [p for p in paq_activos if p.categoria_id in datos.filtro_categoria_ids]
        srv_activos = [s for s in prov.servicios_productos
                       if s.estado == EstadoBasico.ACTIVO and s.deleted_at is None]
        if not paq_activos:
            continue

        # ── Regla 4: Filtrar paquetes sin inventario ANTES del scoring ────
        paq_con_stock = _filtrar_por_inventario(
            paq_activos, datos.fecha_evento_inicio, datos.fecha_evento_fin, db
        )

# ── Fase 3: Elegir paquete ────────────────────────────────────────
        if es_ambiguo:
            pool = paq_con_stock or paq_activos
            mejor = min(pool, key=lambda p: float(p.precio_base or 0))
            score = 10
        elif modo_servicio:
            pool = paq_con_stock or paq_activos
            
            # FIX: Asegurar que el paquete base pertenezca a la categoría detectada
            if tipo_evento:
                pool_filtrado = [p for p in pool if _inferir_tipo_paquete(p) and _norm(_inferir_tipo_paquete(p)) == _norm(tipo_evento)]
            else:
                pool_filtrado = pool
            
            if pool_filtrado:
                mejor = min(pool_filtrado, key=lambda p: float(p.precio_base or 0))
                score = 15  # Puntaje alto porque tiene la categoría correcta
            else:
                # Si el proveedor no tiene paquetes de esta categoría, penalizamos fuertemente
                mejor = min(pool, key=lambda p: float(p.precio_base or 0))
                score = -20
        else:
            mejor, score = _elegir_paquete(
                paq_con_stock or paq_activos, texto, tipo_evento, tematica,
                nombres_tematicas,
            )
            if not mejor:
                pool = paq_con_stock or paq_activos
                mejor = min(pool, key=lambda p: float(p.precio_base or 0))
                score = -20 # Se va al fondo de las alternativas

        incluye = _items_de_paquete(mejor)
        ids_incluidos = {i.servicio_producto_id for i in incluye}

        # ── Validar disponibilidad del paquete elegido ────────────────────
        obs_inv = _validar_disponibilidad(
            incluye, datos.fecha_evento_inicio, datos.fecha_evento_fin, db
        )
        disponible = not obs_inv

        # ── Regla 7: Cross-selling estricto ───────────────────────────────
        adicionales = _cross_sell(
            srv_activos, ids_incluidos, tipo_evento, servicios_pedidos, cantidades,
        ) if not es_ambiguo else []

        total = _r(float(mejor.precio_base or 0) + sum(a.subtotal for a in adicionales))
        observaciones = list(obs_inv)

        if datos.presupuesto_maximo and total > datos.presupuesto_maximo:
            observaciones.append(f"Supera presupuesto de S/ {datos.presupuesto_maximo:.2f}.")
            disponible = False

        puede_pre = disponible and not datos_faltantes
        payload = _payload(datos, prov.id, mejor.id, adicionales, tipo_evento) if puede_pre else None

        rec = ProveedorRecomendado(
            proveedor_id=prov.id, nombre_empresa=prov.nombre_empresa,
            distrito=prov.distrito,
            calificacion_promedio=float(prov.calificacion_promedio) if prov.calificacion_promedio else None,
            paquete=PaqueteRecomendado(
                paquete_id=mejor.id, nombre=mejor.nombre,
                descripcion=mejor.descripcion,
                precio_base=float(mejor.precio_base or 0), incluye=incluye,
            ),
            adicionales_sugeridos=adicionales, total_estimado=total,
            adelanto_20=_r(total * 0.20), saldo_presencial=_r(total * 0.80),
            disponible=disponible, observaciones=observaciones,
            puede_prebloquear=puede_pre,
            datos_faltantes_prebloqueo=datos_faltantes,
            payload_prebloqueo=payload,
        )
        scores[prov.id] = score

        # Regla 8: Penalización vs Diversidad
        if score > 0:
            principales.append(rec)
        else:
            secundarios.append(rec)

    # ── Regla 10: Orden final determinístico ──────────────────────────────
    for lista in [principales, secundarios]:
        lista.sort(key=lambda p: (
            not p.disponible,
            -(scores.get(p.proveedor_id, 0)),
            -(p.calificacion_promedio or 0),
            p.total_estimado if not busca_barato else p.total_estimado,
        ))

    intencion = []
    if tipo_evento:
        intencion.append(tipo_evento)
    if tematica:
        intencion.append(tematica)
    if modo_servicio:
        intencion.append("servicio_directo")
    intencion.extend(sorted(servicios_pedidos))

    requiere_fecha = datos.fecha_evento_inicio is None or datos.fecha_evento_fin is None
    resp_txt = _crear_respuesta(principales, secundarios, requiere_fecha, datos_faltantes, tematica)

    return RecomendacionResponse(
        respuesta=resp_txt,
        accion=_accion(principales + secundarios, datos_faltantes),
        requiere_fecha_hora=requiere_fecha,
        datos_faltantes_prebloqueo=datos_faltantes,
        intencion_detectada=intencion if intencion else ["ambiguo"],
        resultados_principales=principales,
        otras_opciones=secundarios,
    )

# ═══════════════════════════════════════════════════════════════════════════════
# UTILIDADES DE TEXTO
# ═══════════════════════════════════════════════════════════════════════════════
def _norm(texto: str) -> str:
    t = texto.lower()
    for a, b in [("á","a"),("é","e"),("í","i"),("ó","o"),("ú","u"),("ñ","n")]:
        t = t.replace(a, b)
    return t

def _detectar_cantidades(texto: str, aforo: Optional[int]) -> Dict[str, int]:
    c: Dict[str, int] = {}
    for clave, patron in [
        ("dj", r"(\d+)\s*dj"), ("animadora", r"(\d+)\s*animador"),
        ("bailarina", r"(\d+)\s*bailar"), ("muneco", r"(\d+)\s*(muneco|personaje)"),
        ("silla", r"(\d+)\s*silla"), ("toldo", r"(\d+)\s*toldo"), ("mesa", r"(\d+)\s*mesa"),
    ]:
        m = re.search(patron, texto)
        if m:
            c[clave] = int(m.group(1))
    if aforo and "silla" in texto and "silla" not in c:
        c["silla"] = aforo
    return c

def _detecta_bajo_presupuesto(texto: str) -> bool:
    return any(p in texto for p in ["barato", "economico", "bajo presupuesto", "poco dinero", "basico"])

# ═══════════════════════════════════════════════════════════════════════════════
# REGLA 3: SERVICIO AISLADO vs EXPERIENCIA
# ═══════════════════════════════════════════════════════════════════════════════
def _es_servicio_aislado(texto: str, tipo_evento: Optional[str]) -> bool:
    if any(exp in texto for exp in PALABRAS_EXPERIENCIA):
        return False
    return any(srv in texto for srv in SERVICIO_AISLADO)

# ═══════════════════════════════════════════════════════════════════════════════
# REGLA 4: FILTRO DE INVENTARIO PRE-SCORING
# ═══════════════════════════════════════════════════════════════════════════════
def _filtrar_por_inventario(
    paquetes: List[Paquete], inicio: Optional[datetime],
    fin: Optional[datetime], db: Session,
) -> List[Paquete]:
    if not inicio or not fin:
        return paquetes  # Sin fechas no podemos filtrar

    aptos: List[Paquete] = []
    for paq in paquetes:
        todos_disponibles = True
        for det in paq.detalles:
            srv = det.servicio_producto
            if not srv:
                continue
            ocupado = int(
                db.query(func.coalesce(func.sum(OcupacionServicioProducto.cantidad_ocupada), 0))
                .filter(
                    OcupacionServicioProducto.servicio_producto_id == srv.id,
                    OcupacionServicioProducto.fecha_hora_inicio < fin,
                    OcupacionServicioProducto.fecha_hora_fin > inicio,
                ).scalar() or 0
            )
            stock = int(srv.stock_maximo_simultaneo or 0)
            if (stock - ocupado) < int(det.cantidad_incluida or 1):
                todos_disponibles = False
                break
        if todos_disponibles:
            aptos.append(paq)
    return aptos

# ═══════════════════════════════════════════════════════════════════════════════
# REGLA 5: SCORING JERÁRQUICO
# ═══════════════════════════════════════════════════════════════════════════════
def _elegir_paquete(
    paquetes: List[Paquete], texto: str,
    tipo_evento: Optional[str], tematica: Optional[str],
    nombres_tematicas: Set[str],
) -> Tuple[Optional[Paquete], int]:
    mejor: Optional[Paquete] = None
    mejor_score = -999

    for paq in paquetes:
        score = 0
        nom = _norm(f"{paq.nombre or ''} {paq.descripcion or ''}")

        # Nivel 1: CONTEXTO (+20 / -20) — Regla 6: comparar contra categoría del paquete
        if tipo_evento:
            tipo_paq = _inferir_tipo_paquete(paq)
            if tipo_paq and _norm(tipo_paq) == _norm(tipo_evento):
                score += 20
            elif tipo_paq and _norm(tipo_paq) != _norm(tipo_evento):
                score -= 20

        # Nivel 2: TEMÁTICA (+20 / -20)
        if tematica:
            t_n = _norm(tematica)
            if t_n in nom:
                score += 20
            elif _tiene_otra_tematica(nom, "", t_n, nombres_tematicas):
                score -= 20

        # Nivel 3: COINCIDENCIA GENERAL (+5 / +1)
        for palabra in set(texto.split()):
            if len(palabra) < 3 or palabra in STOPWORDS:
                if palabra in nom:
                    score += 1
                continue
            if palabra in nom:
                score += 5

        # Nivel 4: SERVICIOS (+2)
        for det in paq.detalles:
            srv = det.servicio_producto
            if not srv:
                continue
            srv_n = _norm(srv.nombre or "")
            if any(p in srv_n for p in texto.split() if len(p) >= 3 and p not in STOPWORDS):
                score += 2

        if score > mejor_score:
            mejor = paq
            mejor_score = score

    return (mejor, mejor_score) if mejor and mejor_score > 0 else (None, mejor_score)

def _inferir_tipo_paquete(paq: Paquete) -> Optional[str]:
    """Regla 6: Retorna el nombre de categoría del paquete directamente desde la BD."""
    if paq.categoria:
        return paq.categoria.nombre
    return None

def _tiene_otra_tematica(
    nombre: str, tematica_paq: str, buscada: str,
    nombres_tematicas: Set[str],
) -> bool:
    """Detecta si el paquete tiene una temática diferente a la buscada.
    Usa la lista de temáticas de la BD en lugar de un set hardcodeado."""
    combined = f"{nombre} {tematica_paq}"
    return any(t != buscada and t in combined for t in nombres_tematicas)

# ═══════════════════════════════════════════════════════════════════════════════
# INVENTARIO Y DISPONIBILIDAD
# ═══════════════════════════════════════════════════════════════════════════════
def _items_de_paquete(paquete: Paquete) -> List[ItemRecomendado]:
    items: List[ItemRecomendado] = []
    for det in paquete.detalles:
        srv = det.servicio_producto
        if not srv:
            continue
        items.append(ItemRecomendado(
            servicio_producto_id=srv.id, nombre=srv.nombre,
            cantidad=int(det.cantidad_incluida or 1),
            precio_unitario=float(srv.precio_unitario or 0),
            horas=float(srv.duracion_base_horas) if srv.duracion_base_horas else None,
            subtotal=0, tipo=str(srv.tipo.value) if srv.tipo else "",
            motivo="Incluido en paquete base",
            stock_maximo_simultaneo=int(srv.stock_maximo_simultaneo or 0),
        ))
    return items

def _validar_disponibilidad(
    items: List[ItemRecomendado], inicio: Optional[datetime],
    fin: Optional[datetime], db: Session,
) -> List[str]:
    if not inicio or not fin:
        return ["Falta fecha y hora para validar disponibilidad."]
    obs: List[str] = []
    for item in items:
        srv = db.query(ServicioProducto).filter(ServicioProducto.id == item.servicio_producto_id).first()
        if not srv:
            continue
        ocupado = int(
            db.query(func.coalesce(func.sum(OcupacionServicioProducto.cantidad_ocupada), 0))
            .filter(
                OcupacionServicioProducto.servicio_producto_id == srv.id,
                OcupacionServicioProducto.fecha_hora_inicio < fin,
                OcupacionServicioProducto.fecha_hora_fin > inicio,
            ).scalar() or 0
        )
        disp = int(srv.stock_maximo_simultaneo or 0) - ocupado
        if disp < item.cantidad:
            obs.append(f"{srv.nombre}: disponible {disp}, solicitado {item.cantidad}.")
    return obs

# ═══════════════════════════════════════════════════════════════════════════════
# REGLA 7: CROSS-SELLING ESTRICTO
# ═══════════════════════════════════════════════════════════════════════════════
def _cross_sell(
    servicios: List[ServicioProducto], ids_incluidos: Set[int],
    tipo_evento: Optional[str], servicios_pedidos: Set[str],
    cantidades: Dict[str, int],
) -> List[ItemRecomendado]:
    adicionales: List[ItemRecomendado] = []
    # Buscar cross-sell por nombre normalizado de categoría
    palabras_cross: Set[str] = set()
    if tipo_evento:
        tipo_norm = _norm(tipo_evento)
        for clave, palabras in CROSS_SELL.items():
            if _norm(clave) == tipo_norm:
                palabras_cross = palabras
                break

    for srv in servicios:
        if srv.id in ids_incluidos:
            continue
        nom = _norm(srv.nombre or "")

        # SOLO dos caminos: pedido explícito O regla por tipo_evento
        pedido = any(_norm(s) in nom for s in servicios_pedidos)
        relevante = any(_norm(p) in nom for p in palabras_cross) if palabras_cross else False

        if not (pedido or relevante):
            continue

        clave = _clasificar_servicio(nom)
        cantidad = cantidades.get(clave, 1)
        horas = float(srv.duracion_base_horas) if srv.duracion_base_horas else None
        subtotal = _calc_sub(srv, cantidad, horas)

        adicionales.append(ItemRecomendado(
            servicio_producto_id=srv.id, nombre=srv.nombre,
            cantidad=cantidad, precio_unitario=float(srv.precio_unitario or 0),
            horas=horas, subtotal=subtotal,
            tipo=str(srv.tipo.value) if srv.tipo else "",
            motivo="Pedido por el cliente" if pedido else "Sugerido para tu evento",
            stock_maximo_simultaneo=int(srv.stock_maximo_simultaneo or 0),
        ))
    return adicionales[:6]

def _clasificar_servicio(nombre: str) -> str:
    for clave, words in [
        ("dj", ["dj"]), ("animadora", ["animador"]), ("bailarina", ["bailar"]),
        ("muneco", ["muneco", "personaje"]), ("silla", ["silla"]),
        ("toldo", ["toldo", "carpa"]), ("mesa", ["mesa"]),
    ]:
        if any(w in nombre for w in words):
            return clave
    return "servicio"

def _calc_sub(srv: ServicioProducto, cant: int, horas: Optional[float]) -> float:
    precio = float(srv.precio_unitario or 0)
    if horas and (srv.requiere_persona or "dj" in (srv.nombre or "").lower()):
        return _r(precio * cant * horas)
    return _r(precio * cant)

# ═══════════════════════════════════════════════════════════════════════════════
# RESPUESTA Y HELPERS
# ═══════════════════════════════════════════════════════════════════════════════
def _r(v: float) -> float:
    return float(Decimal(str(v)).quantize(Decimal("0.01")))


def _crear_respuesta(
    principales: List[ProveedorRecomendado], secundarios: List[ProveedorRecomendado],
    requiere_fecha: bool, faltantes: List[str], tematica: Optional[str],
) -> str:
    if not principales and not secundarios:
        return "No encontré paquetes para esa búsqueda. Prueba con otra temática, fecha u horario."

    if not principales and secundarios:
        # Antes decía genéricamente "no encontré coincidencias exactas"
        # Ahora es específico con la temática buscada
        if tematica:
            txt = f"No encontré paquetes de '{tematica.title()}' disponibles."
        else:
            txt = "No encontré coincidencias exactas."
        txt += f" Te muestro {len(secundarios)} alternativa{'s' if len(secundarios) > 1 else ''} similar{'es' if len(secundarios) > 1 else ''}."
    else:
        n = len(principales)
        txt = f"Encontré {'una opción ideal' if n == 1 else f'{n} opciones'} que coincide{'n' if n > 1 else ''} con tu búsqueda."
        if tematica:
            txt = txt.replace("tu búsqueda", f"'{tematica.title()}'")
        if secundarios:
            txt += f" También te sugiero {len(secundarios)} alternativas."

    if any(p.puede_prebloquear for p in principales + secundarios):
        txt += " Si alguna te gusta, ya puedes enviarla a prebloqueo."
    elif faltantes:
        txt += f" Para prebloquear necesito: {', '.join(_etiqueta(c) for c in faltantes)}."
    elif requiere_fecha:
        txt += " Necesito fecha y hora para confirmar disponibilidad."
    return txt


def _accion(provs: List[ProveedorRecomendado], faltantes: List[str]) -> str:
    if not provs:
        return "SOLICITAR_DATOS"
    if any(p.puede_prebloquear for p in provs):
        return "PREBLOQUEAR_OPCION"
    if faltantes:
        return "SOLICITAR_DATOS_PREBLOQUEO"
    return "MOSTRAR_OPCIONES"

def _datos_faltantes_prebloqueo(datos: RecomendacionRequest) -> List[str]:
    f: List[str] = []
    if not datos.fecha_evento_inicio:
        f.append("fecha_evento_inicio")
    if not datos.fecha_evento_fin:
        f.append("fecha_evento_fin")
    if not datos.direccion or not datos.direccion.strip():
        f.append("direccion")
    return f

def _payload(
    datos: RecomendacionRequest, prov_id: int, paq_id: int,
    adicionales: List[ItemRecomendado], tipo_evento: Optional[str],
) -> PreReservaCreate:
    return PreReservaCreate(
        proveedor_id=prov_id, paquete_id=paq_id,
        nombre_evento=(datos.nombre_evento or f"{tipo_evento or 'Evento'} Festio").strip(),
        tipo_evento=datos.tipo_evento or tipo_evento,
        fecha_evento_inicio=datos.fecha_evento_inicio,
        fecha_evento_fin=datos.fecha_evento_fin,
        direccion=datos.direccion, aforo_estimado=datos.aforo_estimado,
        adicionales=[
            PreReservaItemCreate(
                servicio_producto_id=a.servicio_producto_id,
                cantidad=a.cantidad, horas_contratadas=a.horas,
            ) for a in adicionales
        ],
    )

def _etiqueta(campo: str) -> str:
    return {"fecha_evento_inicio": "fecha y hora de inicio",
            "fecha_evento_fin": "fecha y hora de fin",
            "direccion": "dirección del evento"}.get(campo, campo)

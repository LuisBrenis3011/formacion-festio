"""
Motor de Recomendación Jerárquico v2.
Consciente del inventario. Comportamiento de vendedor real.
"""
import re
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Set, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.catalogo import DetallePaquete, Paquete, ServicioProducto
from app.models.disponibilidad import OcupacionServicioProducto
from app.models.enums import EstadoBasico, EstadoVerificacion
from app.models.usuario import Proveedor
from app.schemas.chat import (
    ItemRecomendado, PaqueteRecomendado, ProveedorRecomendado,
    RecomendacionRequest, RecomendacionResponse,
)
from app.schemas.reserva import PreReservaCreate, PreReservaItemCreate

# ═══════════════════════════════════════════════════════════════════════════════
# TAXONOMÍA SEPARADA (Regla 1)
# ═══════════════════════════════════════════════════════════════════════════════
TIPOS_EVENTO: Dict[str, Set[str]] = {
    "infantil":   {"show infantil", "baby shower", "revelacion de genero", "fiesta infantil", "infantil", "ninos"},
    "hora_loca":  {"hora loca", "15 anos", "quinceanero", "quinceañera", "boda", "aniversario", "matrimonio"},
    "adultos":    {"chicoteca", "fiesta 20", "dj", "discoteca", "karaoke", "adultos"},
    "mobiliario": {"toldo", "toldos", "silla", "sillas", "mesa", "mesas", "decoracion", "mobiliario", "carpa"},
    "activacion": {"inauguracion", "negocio", "activacion", "corporativo", "empresa"},
}
TEMATICAS: Set[str] = {
    "mario bros", "luigi", "cars", "mickey", "mickey mouse", "minnie", "minnie mouse",
    "pluto", "goofy", "spiderman", "sonic", "granja de zenon", "bartolito",
    "plim plim", "blanca nieves", "elsa", "frozen", "merlina", "kpop",
    "barbie", "minecraft", "princesas", "avengers", "dinosaurios", "unicornio",
    "paw patrol", "peppa pig", "toy story", "moana", "encanto",
}
SERVICIOS_EXTRA: Set[str] = {
    "caritas pintadas", "carita pintada", "burbujas", "burbuja",
    "luces", "luz", "zancos", "zanco", "arlequin",
}
CROSS_SELL: Dict[str, Set[str]] = {
    "infantil":   {"caritas pintadas", "burbujas", "muneco", "personaje"},
    "adultos":    {"luces", "zancos", "arlequin"},
    "hora_loca":  {"luces", "zancos", "arlequin", "bailarin"},
    "mobiliario": {"silla", "mesa", "toldo", "decoracion"},
}
# Palabras de servicio aislado (Regla 3: detectar CASO A)
SERVICIO_AISLADO: Dict[str, str] = {
    "dj": "adultos", "animadora": "infantil", "animador": "infantil",
    "bailarina": "hora_loca", "bailarin": "hora_loca",
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

def recomendar_evento(datos: RecomendacionRequest, db: Session) -> RecomendacionResponse:
    texto = _norm(datos.mensaje)

    # ── Fase 1: Detección jerárquica (Regla 2) ────────────────────────────
    tipo_evento = _detectar_tipo_evento(texto)
    tematica = _detectar_tematica(texto)
    servicios_pedidos = _detectar_servicios_extra(texto)
    cantidades = _detectar_cantidades(texto, datos.aforo_estimado)
    busca_barato = _detecta_bajo_presupuesto(texto)

    # Inferencia jerárquica
    if tipo_evento is None and tematica:
        tipo_evento = "infantil"

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
            joinedload(Proveedor.paquetes).joinedload(Paquete.tematica),
            joinedload(Proveedor.paquetes).joinedload(Paquete.categoria),
            joinedload(Proveedor.servicios_productos),
        )
        .filter(Proveedor.estado_verificacion == EstadoVerificacion.VERIFICADO)
    )
    if datos.distrito:
        query = query.filter(Proveedor.distrito.ilike(f"%{datos.distrito}%"))

    principales: List[ProveedorRecomendado] = []
    secundarios: List[ProveedorRecomendado] = []
    scores: Dict[int, int] = {}  # proveedor_id -> score (Regla 10)

    for prov in query.all():
        paq_activos = [p for p in prov.paquetes if p.estado == EstadoBasico.ACTIVO]
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
            mejor = min(pool, key=lambda p: float(p.precio_base or 0))
            score = 5
        else:
            mejor, score = _elegir_paquete(
                paq_con_stock or paq_activos, texto, tipo_evento, tematica
            )
            if not mejor:
                pool = paq_con_stock or paq_activos
                mejor = min(pool, key=lambda p: float(p.precio_base or 0))
                score = 0

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
# DETECCIÓN JERÁRQUICA (Regla 2)
# ═══════════════════════════════════════════════════════════════════════════════
def _norm(texto: str) -> str:
    t = texto.lower()
    for a, b in [("á","a"),("é","e"),("í","i"),("ó","o"),("ú","u"),("ñ","n")]:
        t = t.replace(a, b)
    return t

def _detectar_tipo_evento(texto: str) -> Optional[str]:
    for tipo, palabras in TIPOS_EVENTO.items():
        for p in palabras:
            if _norm(p) in texto:
                return tipo
    return None

def _detectar_tematica(texto: str) -> Optional[str]:
    for t in sorted(TEMATICAS, key=len, reverse=True):
        if _norm(t) in texto:
            return t
    return None

def _detectar_servicios_extra(texto: str) -> Set[str]:
    return {s for s in SERVICIOS_EXTRA if _norm(s) in texto}

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
) -> Tuple[Optional[Paquete], int]:
    mejor: Optional[Paquete] = None
    mejor_score = -999

    for paq in paquetes:
        score = 0
        nom = _norm(f"{paq.nombre or ''} {paq.descripcion or ''}")
        tem_paq = _norm(paq.tematica.nombre if paq.tematica else "")

        # Nivel 1: CONTEXTO (+20 / -20) — Regla 6: usar categoría primero
        if tipo_evento:
            tipo_paq = _inferir_tipo_paquete(paq)
            if tipo_paq == tipo_evento:
                score += 20
            elif tipo_paq and tipo_paq != tipo_evento:
                score -= 20

        # Nivel 2: TEMÁTICA (+20 / -20)
        if tematica:
            t_n = _norm(tematica)
            if t_n in tem_paq or t_n in nom:
                score += 20
            elif _tiene_otra_tematica(nom, tem_paq, t_n):
                score -= 20

        # Nivel 3: COINCIDENCIA GENERAL (+5 / +1)
        for palabra in set(texto.split()):
            if len(palabra) < 3 or palabra in STOPWORDS:
                if palabra in nom:
                    score += 1
                continue
            if palabra in nom or palabra in tem_paq:
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
    """Regla 6: Priorizar categoría > temática > nombre."""
    # 1. Por categoría del paquete
    if paq.categoria:
        cat = _norm(paq.categoria.nombre or "")
        for tipo, palabras in TIPOS_EVENTO.items():
            if any(_norm(p) in cat for p in palabras):
                return tipo
    # 2. Por temática (si tiene temática → infantil)
    if paq.tematica:
        return "infantil"
    # 3. Fallback: por nombre/descripción
    combined = _norm(f"{paq.nombre or ''} {paq.descripcion or ''}")
    for tipo, palabras in TIPOS_EVENTO.items():
        if any(_norm(p) in combined for p in palabras):
            return tipo
    return None

def _tiene_otra_tematica(nombre: str, tematica_paq: str, buscada: str) -> bool:
    combined = f"{nombre} {tematica_paq}"
    return any(_norm(t) != buscada and _norm(t) in combined for t in TEMATICAS)

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
    palabras_cross = CROSS_SELL.get(tipo_evento or "", set())

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
    if principales:
        n = len(principales)
        txt = f"Encontré {'una opción ideal' if n == 1 else f'{n} opciones'} que coincide{'n' if n > 1 else ''} con tu búsqueda."
        if tematica:
            txt = txt.replace("tu búsqueda", f"'{tematica.title()}'")
        if secundarios:
            txt += f" También te sugiero {len(secundarios)} alternativas."
    else:
        txt = "No encontré coincidencias exactas, pero aquí tienes las mejores alternativas disponibles."
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

from dotenv import load_dotenv
from sqlalchemy.orm import Session

load_dotenv()

from app.domain.chat.schemas import RecomendacionRequest, RecomendacionResponse
from app.services.recomendacion_service import recomendar_evento
from app.services.gemini_service import parsear_mensaje_cliente


def _norm(texto: str) -> str:
    t = texto.lower()
    for a, b in [("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u"), ("ñ", "n")]:
        t = t.replace(a, b)
    return t


def _es_actualizacion_aditiva(mensaje: str) -> bool:
    texto = _norm(mensaje)
    return any(
        palabra in texto
        for palabra in [
            "tambien", "ademas", "adicional", "agrega", "agregar", "anade",
            "anadir", "sumale", "sumar", "incluye", "aparte", "con ",
        ]
    )


def _es_reemplazo_explicito(mensaje: str) -> bool:
    texto = _norm(mensaje)
    return any(
        palabra in texto
        for palabra in [
            "cambia", "cambiar", "cambialo", "reemplaza", "reemplazar",
            "en vez", "mejor que sea", "mejor quiero", "ahora quiero",
        ]
    )


def _unir_listas(actual: list[str], nuevo: list[str]) -> list[str]:
    resultado: list[str] = []
    vistos: set[str] = set()
    for item in [*actual, *nuevo]:
        limpio = item.strip().lower() if isinstance(item, str) else ""
        if limpio and limpio not in vistos:
            resultado.append(limpio)
            vistos.add(limpio)
    return resultado


def fusionar_estado_conversacion(
    estado_actual: RecomendacionRequest | None,
    delta: RecomendacionRequest,
    mensaje: str,
) -> RecomendacionRequest:
    # 1. Iniciamos con el estado base
    estado = estado_actual.model_copy(deep=True) if estado_actual else RecomendacionRequest(mensaje=mensaje)
    estado.mensaje = mensaje

    tipo_previo = estado_actual.tipo_evento if estado_actual else None
    
    # 2. Evaluar si hubo un cambio radical de intención o un reemplazo explícito
    cambio_radical = delta.tipo_evento and tipo_previo and delta.tipo_evento != tipo_previo
    reemplazo = _es_reemplazo_explicito(mensaje)

    # 3. LIMPIEZA DE MEMORIA (El fix principal)
    # Matamos los fantasmas viejos ANTES de meter lo nuevo
    if cambio_radical or reemplazo:
        estado.tematica_detectada = None
        if cambio_radical:
            estado.nombre_evento = None  # Evita arrastrar "Fiesta de Promoción" a un "Show Infantil"
        estado.servicios_extra_detectados = []
        estado.cantidades_servicios = {}

    # 4. APLICAR LOS DATOS NUEVOS EXTRAÍDOS POR GEMINI
    for campo in [
        "nombre_evento",
        "tipo_evento",
        "tematica_detectada",
        "fecha_evento_inicio",
        "fecha_evento_fin",
        "direccion",
        "aforo_estimado",
        "distrito",
        "presupuesto_maximo",
    ]:
        valor = getattr(delta, campo)
        if valor is not None:
            setattr(estado, campo, valor)

    # 5. FUSIONAR LISTAS (Servicios extra y cantidades)
    if not cambio_radical and not reemplazo:
        estado.servicios_extra_detectados = _unir_listas(
            estado.servicios_extra_detectados,
            delta.servicios_extra_detectados or []
        )
        estado.cantidades_servicios = {
            **estado.cantidades_servicios,
            **(delta.cantidades_servicios or {})
        }
    else:
        # Si hubo cambio radical, solo nos quedamos con lo nuevo
        estado.servicios_extra_detectados = delta.servicios_extra_detectados or []
        estado.cantidades_servicios = delta.cantidades_servicios or {}

    # 6. AUTOCOMPLETAR CANTIDADES (El fix del mobiliario vs aforo)
    aforo = estado.aforo_estimado
    if estado.servicios_extra_detectados:
        for srv in estado.servicios_extra_detectados:
            srv_norm = srv.lower()
            if srv_norm not in estado.cantidades_servicios:
                # Si piden sillas/mesas y hay aforo, lo usamos. Si no, 1.
                if "silla" in srv_norm or "mesa" in srv_norm:
                    estado.cantidades_servicios[srv_norm] = aforo if aforo else 1
                else:
                    estado.cantidades_servicios[srv_norm] = 1

    return estado


async def procesar_mensaje(
    mensaje: str,
    historial: list,
    estado_conversacion: RecomendacionRequest | None,
    db: Session,
    filtro_proveedor_ids: list[int] | None = None,
    filtro_categoria_ids: list[int] | None = None,
) -> dict:
    """
    Procesa el mensaje del cliente y retorna recomendaciones.
    """
    delta = await parsear_mensaje_cliente(mensaje, historial, estado_conversacion, db)
    request_estructurado = fusionar_estado_conversacion(estado_conversacion, delta, mensaje)

    # Inyectar filtros del usuario si se proporcionaron
    if filtro_proveedor_ids:
        request_estructurado.filtro_proveedor_ids = filtro_proveedor_ids
    if filtro_categoria_ids:
        request_estructurado.filtro_categoria_ids = filtro_categoria_ids

    print("\n" + "="*50)
    print("GEMINI EXTRAJO DEL TURNO:")
    print(delta.model_dump_json(indent=2))
    print("-"*50)
    print("ESTADO CONVERSACIONAL FUSIONADO:")
    print(request_estructurado.model_dump_json(indent=2))
    print("="*50 + "\n")
    
    resultado: RecomendacionResponse = recomendar_evento(request_estructurado, db)
    resultado.estado_conversacion = request_estructurado
    
    return resultado.model_dump()

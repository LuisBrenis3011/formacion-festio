from dotenv import load_dotenv
from sqlalchemy.orm import Session

load_dotenv()

from app.schemas.chat import RecomendacionRequest, RecomendacionResponse
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
    """
    Mantiene el estado estructurado del evento sin depender de que Gemini
    recuerde todo el historial textual en cada turno.
    """
    estado = estado_actual.model_copy(deep=True) if estado_actual else RecomendacionRequest(mensaje=mensaje)
    aditivo = _es_actualizacion_aditiva(mensaje)
    reemplazo = _es_reemplazo_explicito(mensaje)
    tipo_previo = estado_actual.tipo_evento if estado_actual else None

    estado.mensaje = mensaje

    for campo in [
        "nombre_evento",
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

    if delta.tipo_evento is not None:
        if tipo_previo and aditivo and not reemplazo:
            estado.tipo_evento = tipo_previo
        else:
            estado.tipo_evento = delta.tipo_evento

    estado.servicios_extra_detectados = _unir_listas(
        estado.servicios_extra_detectados,
        delta.servicios_extra_detectados,
    )
    estado.cantidades_servicios = {
        **estado.cantidades_servicios,
        **delta.cantidades_servicios,
    }

    return estado


async def procesar_mensaje(
    mensaje: str,
    historial: list,
    estado_conversacion: RecomendacionRequest | None,
    db: Session,
) -> dict:
    """
    Procesa el mensaje del cliente y retorna recomendaciones.
    """
    delta = await parsear_mensaje_cliente(mensaje, historial, estado_conversacion)
    request_estructurado = fusionar_estado_conversacion(estado_conversacion, delta, mensaje)

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

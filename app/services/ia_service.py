"""
Orquestador IA — Punto de entrada del Asistente Virtual.

MVP: delega al motor de recomendación determinístico.
Producción: reemplazar por OpenAI function calling o similar.
"""
from sqlalchemy.orm import Session

from app.schemas.chat import RecomendacionRequest, RecomendacionResponse
from app.services.recomendacion_service import recomendar_evento


async def procesar_mensaje(
    mensaje: str,
    historial: list,
    db: Session,
) -> dict:
    """
    Procesa el mensaje del cliente y retorna recomendaciones.

    En el MVP actual, extrae intenciones del texto plano y las
    pasa al motor de recomendación. En producción, se reemplazaría
    por un LLM que haga function calling para extraer parámetros
    estructurados (fecha, aforo, temática, presupuesto) del historial
    conversacional y los pase como RecomendacionRequest completo.
    """
    # TODO: Cuando se integre un LLM, parsear el historial para
    # extraer fecha_evento_inicio, fecha_evento_fin, direccion,
    # aforo_estimado, distrito, presupuesto_maximo del contexto
    # conversacional acumulado.

    request = RecomendacionRequest(mensaje=mensaje)
    resultado: RecomendacionResponse = recomendar_evento(request, db)
    return resultado.model_dump()

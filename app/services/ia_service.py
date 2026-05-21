"""
Orquestador IA — Punto de entrada del Asistente Virtual.

MVP: delega al motor de recomendación determinístico.
Producción: reemplazar por OpenAI function calling o similar.
"""
import os
from dotenv import load_dotenv
from sqlalchemy.orm import Session

# Cargar variables de entorno (ej. GEMINI_API_KEY)
load_dotenv()

from app.schemas.chat import RecomendacionRequest, RecomendacionResponse
from app.services.recomendacion_service import recomendar_evento
from app.services.gemini_service import parsear_mensaje_cliente


async def procesar_mensaje(
    mensaje: str,
    historial: list,
    db: Session,
) -> dict:
    """
    Procesa el mensaje del cliente y retorna recomendaciones.
    """
    # Usar el modelo de IA para extraer datos estructurados
    request_estructurado = await parsear_mensaje_cliente(mensaje, historial)

    print("\n" + "="*50)
    print("🤖 GEMINI ENTENDIÓ ESTO:")
    print(request_estructurado.model_dump_json(indent=2))
    print("="*50 + "\n")
    
    # Pasar el request estructurado (ahora con los filtros detectados) al motor
    resultado: RecomendacionResponse = recomendar_evento(request_estructurado, db)
    
    return resultado.model_dump()

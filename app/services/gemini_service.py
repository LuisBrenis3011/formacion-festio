import os
from google import genai
from google.genai import types
from app.schemas.chat import RecomendacionRequest

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("🚨 ¡ALERTA FESTIO! GEMINI_API_KEY no encontrada en el entorno.")

# Inicializamos el cliente pasándole la llave directamente
client = genai.Client(api_key=api_key)

async def parsear_mensaje_cliente(mensaje: str, historial: list) -> RecomendacionRequest:
    """
    Parsea el mensaje actual y el historial usando Gemini para extraer los
    datos estructurados necesarios para la recomendación.
    """
    # 1. Mapeo del historial al formato types.Content de la SDK
    contents = []
    for msg in historial:
        # Extraemos de forma defensiva las claves comunes de un dict de historial
        role = msg.get("role", "user")
        texto = msg.get("content", msg.get("text", ""))
        contents.append(
            types.Content(
                role=role,
                # Usamos instanciación directa de Part para evitar errores de la SDK
                parts=[types.Part(text=texto)] 
            )
        )
    
    # 2. Agregar el mensaje actual como la última entrada del usuario
    contents.append(
        types.Content(
            role="user",
            # Usamos instanciación directa de Part
            parts=[types.Part(text=mensaje)] 
        )
    )

    # 3. Configurar el Structured Output y el System Instruction
    system_instruction = (
        "Eres el motor de IA de Festio, un marketplace de eventos. "
        "Tu objetivo es leer el mensaje actual del usuario y su historial de chat "
        "para extraer todas las variables posibles y estructurarlas según el esquema solicitado. "
        "Rellena los datos faltantes basándote en el contexto. "
        "Si un dato no se menciona en absoluto, déjalo como null."
    )

    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=RecomendacionRequest,
        system_instruction=system_instruction
    )

    # 4. Llamar al modelo de manera asíncrona
    response = await client.aio.models.generate_content(
        model="gemini-3.5-flash",
        contents=contents,
        config=config
    )

    # 5. La SDK parsea automáticamente el resultado al esquema Pydantic si se usa response.parsed
    if hasattr(response, 'parsed') and response.parsed is not None:
        return response.parsed
    
    # Fallback por seguridad en caso de que devuelva el texto plano
    return RecomendacionRequest.model_validate_json(response.text)
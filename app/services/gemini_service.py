import os
from google import genai
from google.genai import types
from app.schemas.chat import RecomendacionRequest, GeminiRecomendacionSchema
from app.services.recomendacion_service import TIPOS_EVENTO, TEMATICAS, SERVICIOS_EXTRA, SERVICIO_AISLADO

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError(" ¡ALERTA FESTIO! GEMINI_API_KEY no encontrada en el entorno.")

# Inicializamos el cliente pasándole la llave directamente
client = genai.Client(api_key=api_key)

async def parsear_mensaje_cliente(mensaje: str, historial: list) -> RecomendacionRequest:
    """
    Parsea el mensaje actual y el historial usando Gemini para extraer los
    datos estructurados necesarios para la recomendación, forzando la 
    normalización ortográfica contra nuestro catálogo.
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

    # 3. Construir catálogos dinámicos
    tipos_oficiales = ", ".join(TIPOS_EVENTO.keys())
    tematicas_oficiales = ", ".join(TEMATICAS)
    todos_los_servicios = ", ".join(SERVICIOS_EXTRA.union(SERVICIO_AISLADO.keys()))

    # 4. Configurar el Structured Output y el System Instruction Dinámico
    system_instruction = f"""
    Eres el motor de IA de Festio, un marketplace de eventos en Perú. 
    Lee el mensaje del usuario y su historial para extraer datos estructurados. 
    Si un dato no se menciona, déjalo null o lista vacía según corresponda.

    REGLAS CRÍTICAS DE NORMALIZACIÓN:
    El usuario escribirá con errores ortográficos (ej. "mario bross", "spaiderman", "karitas pintadas").
    Debes corregirlos y MAPEARLOS OBLIGATORIAMENTE a nuestro catálogo oficial. Si pide algo fuera de la lista, devuelve null.

    - tipo_evento: clasifica SOLO en uno de estos valores: [{tipos_oficiales}]. Usa 'infantil' si menciona niños o personajes. null si no queda claro.
    - tematica_detectada: corrige ortografía y mapea EXACTAMENTE a uno de estos: [{tematicas_oficiales}]. null si no hay o no existe en la lista.
    - servicios_extra_detectados: corrige y mapea EXACTAMENTE a elementos de esta lista: [{todos_los_servicios}]. Lista vacía si no hay.
    - cantidades_servicios: lista de objetos con cantidades si las menciona (ej: [{{"nombre_servicio": "bailarin", "cantidad": 3}}, {{"nombre_servicio": "dj", "cantidad": 1}}]). Lista vacía si no hay.
    - aforo_estimado: número de personas si lo menciona. null si no.
    - distrito: distrito o zona de Lima si lo menciona. null si no.
    - presupuesto_maximo: monto en soles si menciona un límite de precio. null si no.
    - direccion: dirección exacta si la da. null si no.
    
    Rellena también con el contexto del historial si el usuario aclaró algo antes.
    """

    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=GeminiRecomendacionSchema,
        system_instruction=system_instruction
    )

    # 5. Llamar al modelo de manera asíncrona
    response = await client.aio.models.generate_content(
        model="gemini-3.5-flash",
        contents=contents,
        config=config
    )

    # 6. La SDK parsea automáticamente el resultado al esquema Pydantic
    if hasattr(response, 'parsed') and response.parsed is not None:
        return response.parsed.to_recomendacion_request()
    
    # Fallback por seguridad en caso de que devuelva el texto plano
    gemini_data = GeminiRecomendacionSchema.model_validate_json(response.text)
    return gemini_data.to_recomendacion_request()
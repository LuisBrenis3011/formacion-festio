import os
from google import genai
from google.genai import types
from app.schemas.chat import RecomendacionRequest, GeminiRecomendacionSchema
from app.services.recomendacion_service import TIPOS_EVENTO, TEMATICAS, SERVICIOS_DETECTABLES

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError(" ¡ALERTA FESTIO! GEMINI_API_KEY no encontrada en el entorno.")

# Inicializamos el cliente pasándole la llave directamente
client = genai.Client(api_key=api_key)

async def parsear_mensaje_cliente(
    mensaje: str,
    historial: list,
    estado_actual: RecomendacionRequest | None = None,
) -> RecomendacionRequest:
    """
    Parsea el mensaje actual y el historial usando Gemini para extraer los
    datos estructurados necesarios para la recomendación, forzando la 
    normalización ortográfica contra nuestro catálogo.
    """
    # Gemini extrae solo el delta del turno actual. El estado acumulado se
    # fusiona de forma deterministica en Python.
    contents = [
        types.Content(
            role="user",
            parts=[types.Part(text=mensaje)]
        )
    ]

    # 3. Construir catálogos dinámicos
    tipos_oficiales = ", ".join(TIPOS_EVENTO.keys())
    tematicas_oficiales = ", ".join(TEMATICAS)
    servicios_sugeridos = ", ".join(sorted(SERVICIOS_DETECTABLES))
    estado_json = (
        estado_actual.model_dump_json(exclude_none=True)
        if estado_actual
        else "{}"
    )

    # 4. Configurar el Structured Output y el System Instruction Dinámico
    system_instruction = f"""
    Eres el motor de IA de Festio, un marketplace de eventos en Perú. 
    Lee SOLO el mensaje actual del usuario para extraer los datos nuevos o
    modificados. El backend ya conserva el estado acumulado.
    Estado estructurado actual, solo como referencia:
    {estado_json}

    Si un dato no se menciona en el mensaje actual, déjalo null o lista vacía
    según corresponda. No copies datos antiguos del estado.

    REGLAS CRÍTICAS DE NORMALIZACIÓN:
    El usuario escribirá con errores ortográficos (ej. "mario bross", "spaiderman", "karitas pintadas").
    Debes corregirlos y MAPEARLOS OBLIGATORIAMENTE a nuestro catálogo oficial. Si pide algo fuera de la lista, devuelve null.

    - mensaje: devuelve exactamente el mensaje actual, sin repetirlo ni concatenarlo.
    - tipo_evento: clasifica SOLO en uno de estos valores: [{tipos_oficiales}]. Usa 'infantil' si menciona niños. null si no queda claro. Si el usuario solo agrega un servicio con palabras como "también", "además", "agrega", "con" o "aparte", deja tipo_evento null salvo que pida cambiar el evento principal.
    - tematica_detectada: corrige ortografía y mapea EXACTAMENTE a uno de estos: [{tematicas_oficiales}]. null si no hay o no existe en la lista.
    - servicios_extra_detectados: servicios, productos o adicionales pedidos en el mensaje actual. Normaliza a nombres cortos en minúscula. Usa estos nombres como referencia cuando apliquen: [{servicios_sugeridos}]. Si el usuario pide algo que no aparece en la lista, igual inclúyelo con un nombre breve y normalizado. Lista vacía si no hay.
    - cantidades_servicios: lista de objetos con cantidades si las menciona (ej: [{{"nombre_servicio": "bailarin", "cantidad": 3}}, {{"nombre_servicio": "dj", "cantidad": 1}}]). Lista vacía si no hay.
    - aforo_estimado: número de personas si lo menciona. null si no.
    - distrito: distrito o zona de Lima si lo menciona. null si no.
    - presupuesto_maximo: monto en soles si menciona un límite de precio. null si no.
    - direccion: dirección exacta si la da. null si no.
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
        request = response.parsed.to_recomendacion_request()
    else:
        request = GeminiRecomendacionSchema.model_validate_json(response.text).to_recomendacion_request()

    request.mensaje = mensaje
    return request

import os
import asyncio
from google import genai
from google.genai import types, errors
from sqlalchemy.orm import Session

from app.models.catalogo import Categoria, ServicioProducto, Tematica
from app.schemas.chat import RecomendacionRequest, GeminiRecomendacionSchema

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError(" ¡ALERTA FESTIO! GEMINI_API_KEY no encontrada en el entorno.")

# Inicializamos el cliente pasándole la llave directamente
client = genai.Client(api_key=api_key)

for model in client.models.list():
    print(model.name)

async def parsear_mensaje_cliente(
    mensaje: str,
    historial: list,
    estado_actual: RecomendacionRequest | None = None,
    db: Session = None,
) -> RecomendacionRequest:
    """
    Parsea el mensaje actual y el historial usando Gemini para extraer los
    datos estructurados necesarios para la recomendación, forzando la 
    normalización ortográfica contra nuestro catálogo dinámico desde la BD.
    """
    # Gemini extrae solo el delta del turno actual. El estado acumulado se
    # fusiona de forma deterministica en Python.
    contents = [
        types.Content(
            role="user",
            parts=[types.Part(text=mensaje)]
        )
    ]

    # 3. Construir catálogos dinámicos desde la base de datos
    categorias_db = db.query(Categoria).all() if db else []
    tematicas_db = db.query(Tematica).all() if db else []
    servicios_db = (
        db.query(ServicioProducto.nombre).distinct().all() if db else []
    )

    tipos_oficiales = ", ".join([c.nombre for c in categorias_db])
    tematicas_oficiales = ", ".join([t.nombre for t in tematicas_db])
    servicios_sugeridos = ", ".join(sorted({s[0] for s in servicios_db}))

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
    - tipo_evento: clasifica SIEMPRE en uno de estos valores: [{tipos_oficiales}]. Clasifica según lo que el usuario PIDE en este mensaje, incluso si usa palabras como "también", "además" o "aparte". Ejemplos: "quiero alquilar sillas" → "Mobiliario y Decoración", "quiero un show infantil" → "Shows Infantiles", "necesito un DJ" → "Personal y Música". Usa 'Shows Infantiles' si menciona niños o temáticas infantiles. null SOLO si el mensaje no contiene ninguna pista de categoría (ej. solo da una dirección o fecha).
    - tematica_detectada: corrige ortografía y mapea EXACTAMENTE a uno de estos: [{tematicas_oficiales}]. null si no hay o no existe en la lista. IMPORTANTE: si el usuario pide algo de una categoría que no tiene temáticas (ej. sillas, toldos, DJ), devuelve null.
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
    max_reintentos = 3
    response = None
    modelo_actual = "gemini-2.5-flash"
    
    for intento in range(max_reintentos):
        try:
            response = await client.aio.models.generate_content(
                model=modelo_actual,
                contents=contents,
                config=config
            )
            break  # Si la llamada es exitosa, rompemos el bucle
            
        except errors.ServerError as e:
            if e.code == 503 and intento < max_reintentos - 1:
                tiempo_espera = 2 ** intento  
                print(f"Servidor de {modelo_actual} saturado. Reintentando en {tiempo_espera}s...")
                await asyncio.sleep(tiempo_espera)
            else:
                # Si falló las 3 veces o es un error distinto a 503, lanzamos la excepción
                print(f"Error crítico de API tras {max_reintentos} intentos: {e}")
                raise e

    # 6. La SDK parsea automáticamente el resultado al esquema Pydantic
    if hasattr(response, 'parsed') and response.parsed is not None:
        request = response.parsed.to_recomendacion_request()
    else:
        request = GeminiRecomendacionSchema.model_validate_json(response.text).to_recomendacion_request()

    request.mensaje = mensaje
    return request

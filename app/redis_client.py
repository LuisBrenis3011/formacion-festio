import redis
from app.config import settings

# Cliente Redis para bloqueos temporales de inventario
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

BLOQUEO_TTL_SEGUNDOS = 600  # 10 minutos

def bloquear_inventario(reserva_key: str, datos: dict) -> bool:
    """Bloquea el inventario por 10 minutos en Redis."""
    import json
    return redis_client.setex(
        name=f"bloqueo:{reserva_key}",
        time=BLOQUEO_TTL_SEGUNDOS,
        value=json.dumps(datos)
    )

def liberar_inventario(reserva_key: str) -> bool:
    """Libera el bloqueo del inventario manualmente."""
    return redis_client.delete(f"bloqueo:{reserva_key}") > 0

def obtener_bloqueo(reserva_key: str) -> dict | None:
    """Verifica si existe un bloqueo activo."""
    import json
    data = redis_client.get(f"bloqueo:{reserva_key}")
    return json.loads(data) if data else None

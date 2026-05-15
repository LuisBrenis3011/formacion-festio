import json
import time
from typing import Optional
from redis.exceptions import RedisError
from app.redis_client import redis_client, BLOQUEO_TTL_SEGUNDOS

_MEMORY_BLOQUEOS: dict[str, tuple[float, dict]] = {}


def generar_key(reserva_temp_id: str) -> str:
    return f"bloqueo:reserva:{reserva_temp_id}"


def crear_bloqueo(reserva_temp_id: str, datos: dict) -> bool:
    """
    Bloquea el inventario por 10 minutos en Redis.
    Si el cliente no paga en ese tiempo, Redis elimina
    la llave automáticamente y libera el inventario.
    """
    key = generar_key(reserva_temp_id)
    try:
        return redis_client.setex(
            name=key,
            time=BLOQUEO_TTL_SEGUNDOS,
            value=json.dumps(datos, default=str),
        )
    except RedisError:
        _MEMORY_BLOQUEOS[key] = (time.time() + BLOQUEO_TTL_SEGUNDOS, datos)
        return True


def obtener_bloqueo(reserva_temp_id: str) -> Optional[dict]:
    """
    Retorna los datos del bloqueo si aún está activo.
    Retorna None si ya expiró o no existe.
    """
    key = generar_key(reserva_temp_id)
    try:
        data = redis_client.get(key)
        return json.loads(data) if data else None
    except RedisError:
        _limpiar_memoria()
        item = _MEMORY_BLOQUEOS.get(key)
        return item[1] if item else None


def liberar_bloqueo(reserva_temp_id: str) -> bool:
    """Elimina el bloqueo manualmente (pago exitoso o cancelación)."""
    key = generar_key(reserva_temp_id)
    try:
        return redis_client.delete(key) > 0
    except RedisError:
        return _MEMORY_BLOQUEOS.pop(key, None) is not None


def tiempo_restante(reserva_temp_id: str) -> int:
    """Retorna los segundos restantes del bloqueo. 0 si ya expiró."""
    key = generar_key(reserva_temp_id)
    try:
        ttl = redis_client.ttl(key)
        return max(ttl, 0)
    except RedisError:
        _limpiar_memoria()
        item = _MEMORY_BLOQUEOS.get(key)
        if not item:
            return 0
        return max(int(item[0] - time.time()), 0)


def listar_bloqueos() -> list[dict]:
    """Lista bloqueos activos para considerar pre-reservas en disponibilidad."""
    try:
        bloqueos = []
        for key in redis_client.scan_iter(match="bloqueo:reserva:*"):
            data = redis_client.get(key)
            if data:
                bloqueos.append(json.loads(data))
        return bloqueos
    except RedisError:
        _limpiar_memoria()
        return [datos for _, datos in _MEMORY_BLOQUEOS.values()]


def _limpiar_memoria() -> None:
    ahora = time.time()
    expirados = [key for key, (vence, _) in _MEMORY_BLOQUEOS.items() if vence <= ahora]
    for key in expirados:
        _MEMORY_BLOQUEOS.pop(key, None)

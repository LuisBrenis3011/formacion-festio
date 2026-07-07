import json
from datetime import date, datetime
from typing import Optional

from fastapi import HTTPException
from redis.exceptions import RedisError

from app.redis_client import redis_client


_KEY_PREFIX = "calendario:proveedor"
_MEMORY_BLOQUEOS: dict[str, dict] = {}


def listar_bloqueos(proveedor_id: int) -> list[dict]:
    hoy = date.today()
    items = [
        item for item in _listar_items_proveedor(proveedor_id)
        if date.fromisoformat(item["fecha"]) >= hoy
    ]
    items.sort(key=lambda item: item["fecha"])
    return items


def crear_bloqueo(proveedor_id: int, fecha: date, motivo: Optional[str] = None) -> dict:
    if fecha < date.today():
        raise HTTPException(status_code=400, detail="No se puede bloquear una fecha pasada")

    if obtener_bloqueo(proveedor_id, fecha):
        raise HTTPException(status_code=409, detail="La fecha ya está bloqueada para este proveedor")

    payload = {
        "fecha": fecha.isoformat(),
        "motivo": (motivo or "").strip() or None,
        "created_at": datetime.utcnow().isoformat(),
    }
    _guardar_payload(_build_key(proveedor_id, fecha), payload)
    return payload


def eliminar_bloqueo(proveedor_id: int, fecha: date) -> None:
    key = _build_key(proveedor_id, fecha)
    if not _payload_exists(key):
        raise HTTPException(status_code=404, detail="Bloqueo no encontrado")

    try:
        redis_client.delete(key)
    except RedisError:
        pass
    _MEMORY_BLOQUEOS.pop(key, None)


def obtener_bloqueo(proveedor_id: int, fecha: date) -> Optional[dict]:
    return _leer_payload(_build_key(proveedor_id, fecha))


def obtener_bloqueo_evento(proveedor_id: int, fecha_evento_inicio: datetime) -> Optional[dict]:
    return obtener_bloqueo(proveedor_id, fecha_evento_inicio.date())


def detalle_fecha_bloqueada(proveedor_id: int, fecha_evento_inicio: datetime) -> Optional[str]:
    bloqueo = obtener_bloqueo_evento(proveedor_id, fecha_evento_inicio)
    if not bloqueo:
        return None

    motivo = bloqueo.get("motivo")
    if motivo:
        return f"Fecha bloqueada por el proveedor. Motivo: {motivo}"
    return "Fecha bloqueada por el proveedor"


def _listar_items_proveedor(proveedor_id: int) -> list[dict]:
    pattern = f"{_KEY_PREFIX}:{proveedor_id}:*"
    try:
        items: list[dict] = []
        for key in redis_client.scan_iter(match=pattern):
            payload = redis_client.get(key)
            if payload:
                items.append(json.loads(payload))
        return items
    except RedisError:
        return [
            payload for key, payload in _MEMORY_BLOQUEOS.items()
            if key.startswith(pattern[:-1])
        ]


def _payload_exists(key: str) -> bool:
    if key in _MEMORY_BLOQUEOS:
        return True
    try:
        return bool(redis_client.exists(key))
    except RedisError:
        return False


def _guardar_payload(key: str, payload: dict) -> None:
    try:
        redis_client.set(key, json.dumps(payload, default=str))
    except RedisError:
        pass
    _MEMORY_BLOQUEOS[key] = payload


def _leer_payload(key: str) -> Optional[dict]:
    if key in _MEMORY_BLOQUEOS:
        return _MEMORY_BLOQUEOS[key]
    try:
        payload = redis_client.get(key)
        return json.loads(payload) if payload else None
    except RedisError:
        return None


def _build_key(proveedor_id: int, fecha: date) -> str:
    return f"{_KEY_PREFIX}:{proveedor_id}:{fecha.isoformat()}"

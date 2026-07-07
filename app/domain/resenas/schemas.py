from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class ResenaPublicaCreate(BaseModel):
    """Schema para crear una reseña pública (sin reserva asociada)."""
    proveedor_id: int
    calificacion: int = Field(ge=1, le=5)
    comentario: Optional[str] = Field(None, max_length=500)


class ResenaPublicaOut(BaseModel):
    """Schema de salida para reseñas públicas — incluye nombre del usuario."""
    id: int
    proveedor_id: int
    calificacion: int
    comentario: Optional[str]
    fecha: datetime
    nombre_usuario: str  # nombre del usuario que dejó la reseña

    model_config = ConfigDict(from_attributes=True)


# ── Market Analytics (Proveedor) ──────────────────────────────────────────────

class TopPaqueteOut(BaseModel):
    paquete_id: int
    nombre: str
    ventas: int
    porcentaje: int


class ResenaRecienteOut(BaseModel):
    id: int
    cliente_nombre: str
    calificacion: int
    comentario: Optional[str] = None
    fecha: str  # ISO 8601


class MarketAnalyticsOut(BaseModel):
    calificacion_promedio: float
    total_resenas: int
    distribucion_estrellas: dict[int, int]
    top_paquetes: list[TopPaqueteOut]
    resenas_recientes: list[ResenaRecienteOut]

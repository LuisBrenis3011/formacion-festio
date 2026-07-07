from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


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

    class Config:
        from_attributes = True

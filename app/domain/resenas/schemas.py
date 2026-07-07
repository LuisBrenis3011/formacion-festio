from datetime import datetime
from typing import Optional, Dict, List

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


class TopPaqueteOut(BaseModel):
    paquete_id: int
    nombre: str
    ventas: int
    porcentaje: float


class ResenaRecienteOut(BaseModel):
    id: int
    cliente_nombre: str
    calificacion: int
    comentario: Optional[str] = None
    fecha: datetime


class MarketAnalyticsOut(BaseModel):
    calificacion_promedio: float
    total_resenas: int
    distribucion_estrellas: Dict[int, int]
    top_paquetes: List[TopPaqueteOut]
    resenas_recientes: List[ResenaRecienteOut]
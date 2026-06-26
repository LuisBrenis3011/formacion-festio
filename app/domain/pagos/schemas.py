from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.domain.common.enums import (
    CanalNotificacion,
    EstadoNotificacion,
    EstadoPago,
    MetodoPago,
    TipoComprobante,
    TipoNotificacion,
    TipoPago,
)


class PagoCreate(BaseModel):
    reserva_id: int
    tipo_pago: TipoPago
    monto: float = Field(..., gt=0)
    metodo_pago: MetodoPago
    codigo_transaccion: Optional[str] = None


class PagoOut(BaseModel):
    id: int
    reserva_id: int
    tipo_pago: TipoPago
    monto: float
    metodo_pago: MetodoPago
    estado: EstadoPago
    codigo_transaccion: Optional[str]
    fecha_pago: datetime

    class Config:
        from_attributes = True


class ComprobanteOut(BaseModel):
    id: int
    reserva_id: int
    pago_id: int
    tipo: TipoComprobante
    numero_comprobante: str
    fecha_emision: datetime
    url_pdf: Optional[str]

    class Config:
        from_attributes = True


class ResenaCreate(BaseModel):
    reserva_id: int
    cliente_id: int
    proveedor_id: int
    calificacion: int = Field(..., ge=1, le=5)
    comentario: Optional[str] = Field(None, max_length=500)


class ResenaOut(BaseModel):
    id: int
    reserva_id: int
    cliente_id: int
    proveedor_id: int
    calificacion: int
    comentario: Optional[str]
    fecha: datetime

    class Config:
        from_attributes = True


class NotificacionCreate(BaseModel):
    usuario_id: int
    reserva_id: Optional[int] = None
    tipo: TipoNotificacion
    mensaje: str = Field(..., min_length=1, max_length=500)
    canal: CanalNotificacion


class NotificacionOut(BaseModel):
    id: int
    usuario_id: int
    reserva_id: Optional[int]
    tipo: TipoNotificacion
    mensaje: str
    canal: CanalNotificacion
    estado: EstadoNotificacion
    fecha_envio: datetime

    class Config:
        from_attributes = True


from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator, ConfigDict

from app.domain.common.enums import EstadoReserva

from app.domain.common.enums import MetodoPago


# ── Validadores de fecha ──────────────────────────────────────────────────────

def _validar_fecha_futura(v: datetime, campo: str) -> datetime:
    """Rechaza fechas en el pasado."""
    ahora = datetime.now(v.tzinfo) if v.tzinfo else datetime.now()
    if v < ahora:
        raise ValueError(f"{campo} no puede ser una fecha en el pasado")
    return v


class EventoCreate(BaseModel):
    cliente_id: int
    categoria_id: Optional[int] = None
    nombre_evento: str = Field(..., min_length=3, max_length=200)
    tipo_evento: Optional[str] = Field(None, max_length=100)
    fecha_evento_inicio: datetime
    fecha_evento_fin: datetime
    direccion: str = Field(..., min_length=3, max_length=300)
    aforo_estimado: Optional[int] = Field(None, gt=0)

    @field_validator("fecha_evento_inicio")
    @classmethod
    def inicio_no_pasado(cls, v: datetime) -> datetime:
        return _validar_fecha_futura(v, "fecha_evento_inicio")

    @model_validator(mode="after")
    def fin_despues_de_inicio(self):
        if self.fecha_evento_fin <= self.fecha_evento_inicio:
            raise ValueError("fecha_evento_fin debe ser posterior a fecha_evento_inicio")
        return self


class EventoOut(BaseModel):
    id: int
    cliente_id: int
    categoria_id: Optional[int]
    nombre_evento: str
    tipo_evento: Optional[str]
    fecha_evento_inicio: datetime
    fecha_evento_fin: datetime
    direccion: str
    aforo_estimado: Optional[int]

    class Config:
        from_attributes = True


class DetalleReservaPersonalCreate(BaseModel):
    personal_id: int


class DetalleReservaPersonalOut(BaseModel):
    id: int
    personal_id: int
    fecha_asignacion: datetime

    class Config:
        from_attributes = True


class DetalleReservaCreate(BaseModel):
    paquete_id: Optional[int] = None
    servicio_producto_id: Optional[int] = None
    cantidad: int = Field(1, gt=0)
    horas_contratadas: Optional[float] = Field(None, gt=0)
    fecha_hora_inicio_servicio: Optional[datetime] = None
    fecha_hora_fin_servicio: Optional[datetime] = None


class DetalleReservaOut(BaseModel):
    id: int
    reserva_id: int
    paquete_id: Optional[int]
    servicio_producto_id: Optional[int]
    cantidad: int
    horas_contratadas: Optional[float]
    precio_unitario: float
    subtotal: float
    fecha_hora_inicio_servicio: Optional[datetime]
    fecha_hora_fin_servicio: Optional[datetime]
    personal_asignado: List[DetalleReservaPersonalOut]

    class Config:
        from_attributes = True


class ReservaCreate(BaseModel):
    evento_id: int
    proveedor_id: int
    tematica_id: Optional[int] = None
    detalles: List[DetalleReservaCreate]


class PreReservaItemCreate(BaseModel):
    servicio_producto_id: int
    cantidad: int = Field(1, gt=0)
    horas_contratadas: Optional[float] = Field(None, gt=0)


class PreReservaDetalleOut(BaseModel):
    paquete_id: Optional[int] = None
    servicio_producto_id: Optional[int] = None
    nombre: str
    tipo: str
    cantidad: int
    horas_contratadas: Optional[float] = None
    precio_unitario: float
    subtotal: float


class PreReservaCreate(BaseModel):
    proveedor_id: int
    paquete_id: int
    nombre_evento: str = Field(..., min_length=3, max_length=200)
    tipo_evento: Optional[str] = Field(None, max_length=100)
    fecha_evento_inicio: datetime
    fecha_evento_fin: datetime
    direccion: str = Field(..., min_length=3, max_length=300)
    aforo_estimado: Optional[int] = Field(None, gt=0)
    adicionales: List[PreReservaItemCreate] = []

    @field_validator("fecha_evento_inicio")
    @classmethod
    def inicio_no_pasado(cls, v: datetime) -> datetime:
        return _validar_fecha_futura(v, "fecha_evento_inicio")

    @model_validator(mode="after")
    def fin_despues_de_inicio(self):
        if self.fecha_evento_fin <= self.fecha_evento_inicio:
            raise ValueError("fecha_evento_fin debe ser posterior a fecha_evento_inicio")
        return self


class PreReservaResponse(BaseModel):
    reserva_temp_id: str
    proveedor_id: int
    paquete_id: int
    monto_total: float
    monto_adelanto: float
    monto_pendiente: float
    minutos_restantes: int
    detalles: List[PreReservaDetalleOut]
    mensaje: str


class CheckoutClienteCreate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
    apellido: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    telefono: Optional[str] = Field(None, max_length=20)
    password: Optional[str] = Field(None, min_length=8, max_length=128)
    direccion: Optional[str] = Field(None, max_length=300)
    metodo_pago: str = "TARJETA"


class CheckoutReservaResponse(BaseModel):
    reserva_id: int
    evento_id: int
    cliente_id: int
    pago_id: int
    estado_pago: str
    monto_total: float
    monto_adelanto: float
    monto_pendiente: float
    mensaje: str


class ReservaOut(BaseModel):
    id: int
    evento_id: int
    proveedor_id: int
    tematica_id: Optional[int]
    estado: EstadoReserva
    monto_total: float
    costo_movilidad: float
    monto_adelanto: float
    monto_pendiente: float
    fecha_creacion: datetime
    detalles: List[DetalleReservaOut]

    class Config:
        from_attributes = True


class ConsultaDisponibilidadRequest(BaseModel):
    proveedor_id: int
    fecha_evento_inicio: datetime
    fecha_evento_fin: datetime
    detalles: List[DetalleReservaCreate]

    @field_validator("fecha_evento_inicio")
    @classmethod
    def inicio_no_pasado(cls, v: datetime) -> datetime:
        return _validar_fecha_futura(v, "fecha_evento_inicio")

    @model_validator(mode="after")
    def fin_despues_de_inicio(self):
        if self.fecha_evento_fin <= self.fecha_evento_inicio:
            raise ValueError("fecha_evento_fin debe ser posterior a fecha_evento_inicio")
        return self


class DisponibilidadResponse(BaseModel):
    disponible: bool
    mensaje: str
    items_no_disponibles: Optional[List[str]] = None


class MisReservasDetalleOut(BaseModel):
    nombre: str
    tipo: str  # "paquete" | "adicional"
    cantidad: int
    subtotal: float

    class Config:
        from_attributes = True


class MisReservasItemOut(BaseModel):
    reserva_id: int
    estado: str
    nombre_evento: str
    tipo_evento: Optional[str] = None
    fecha_evento_inicio: datetime
    fecha_evento_fin: datetime
    direccion: str
    nombre_empresa: str
    monto_total: float
    monto_adelanto: float
    monto_pendiente: float
    fecha_creacion: datetime
    detalles: List[MisReservasDetalleOut]

    class Config:
        from_attributes = True

class CompletarReservaRequest(BaseModel):
    metodo_pago: MetodoPago = MetodoPago.EFECTIVO
    codigo_transaccion: Optional[str] = Field(None, max_length=150)


class CompletarReservaResponse(BaseModel):
    reserva_id: int
    estado: str
    pago_id: int
    monto_pagado: float
    mensaje: str


class ProveedorReservaItemOut(BaseModel):
    reserva_id: int
    estado: str
    nombre_evento: str
    tipo_evento: Optional[str] = None
    fecha_evento_inicio: datetime
    fecha_evento_fin: datetime
    direccion: str
    nombre_cliente: str
    monto_total: float
    monto_adelanto: float
    monto_pendiente: float
    fecha_creacion: datetime
    detalles: List[MisReservasDetalleOut]

    model_config = ConfigDict(from_attributes=True)
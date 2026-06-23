from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.models.enums import EstadoReserva


class EventoCreate(BaseModel):
    cliente_id: int
    categoria_id: Optional[int] = None
    nombre_evento: str
    tipo_evento: Optional[str] = None
    fecha_evento_inicio: datetime
    fecha_evento_fin: datetime
    direccion: str
    aforo_estimado: Optional[int] = None


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
    cantidad: int = 1
    horas_contratadas: Optional[float] = None
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
    cantidad: int = 1
    horas_contratadas: Optional[float] = None


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
    nombre_evento: str
    tipo_evento: Optional[str] = None
    fecha_evento_inicio: datetime
    fecha_evento_fin: datetime
    direccion: str
    aforo_estimado: Optional[int] = None
    adicionales: List[PreReservaItemCreate] = []


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
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    email: Optional[str] = None
    telefono: Optional[str] = None
    password: Optional[str] = None
    direccion: Optional[str] = None
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


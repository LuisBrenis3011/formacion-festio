from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.reserva import PreReservaCreate


class ChatRequest(BaseModel):
    mensaje: str
    historial: List[dict] = []


class RecomendacionRequest(BaseModel):
    mensaje: str
    nombre_evento: Optional[str] = None
    tipo_evento: Optional[str] = None
    fecha_evento_inicio: Optional[datetime] = None
    fecha_evento_fin: Optional[datetime] = None
    direccion: Optional[str] = None
    aforo_estimado: Optional[int] = None
    distrito: Optional[str] = None
    presupuesto_maximo: Optional[float] = None


class ItemRecomendado(BaseModel):
    servicio_producto_id: int
    nombre: str
    cantidad: int
    precio_unitario: float
    horas: Optional[float] = None
    subtotal: float
    tipo: str
    motivo: str
    stock_maximo_simultaneo: Optional[int] = None


class PaqueteRecomendado(BaseModel):
    paquete_id: int
    nombre: str
    descripcion: Optional[str]
    precio_base: float
    incluye: List[ItemRecomendado]


class ProveedorRecomendado(BaseModel):
    proveedor_id: int
    nombre_empresa: str
    distrito: Optional[str]
    calificacion_promedio: Optional[float]
    paquete: PaqueteRecomendado
    adicionales_sugeridos: List[ItemRecomendado]
    total_estimado: float
    adelanto_20: float
    saldo_presencial: float
    disponible: bool
    observaciones: List[str]
    puede_prebloquear: bool = False
    datos_faltantes_prebloqueo: List[str] = Field(default_factory=list)
    payload_prebloqueo: Optional[PreReservaCreate] = None


class RecomendacionResponse(BaseModel):
    respuesta: str
    accion: str
    requiere_fecha_hora: bool
    datos_faltantes_prebloqueo: List[str] = Field(default_factory=list)
    endpoint_prebloqueo: str = "/api/reservas/prebloquear"
    intencion_detectada: List[str]
    resultados_principales: List[ProveedorRecomendado] = Field(default_factory=list)
    otras_opciones: List[ProveedorRecomendado] = Field(default_factory=list)

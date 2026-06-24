from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from app.domain.reservas.schemas import PreReservaCreate


class CantidadServicio(BaseModel):
    """Par clave-valor para cantidades de servicios.
    El SDK google-genai no soporta dict[str, int] en Structured Output
    (genera additionalProperties que types.Schema rechaza),
    así que usamos este modelo tipado para la interfaz con Gemini."""
    nombre_servicio: str
    cantidad: int


class RecomendacionRequest(BaseModel):
    mensaje: str
    nombre_evento: Optional[str] = None
    tipo_evento: Optional[str] = None
    tematica_detectada: Optional[str] = None        
    servicios_extra_detectados: list[str] = Field(default_factory=list)
    cantidades_servicios: dict[str, int] = Field(default_factory=dict)
    fecha_evento_inicio: Optional[datetime] = None
    fecha_evento_fin: Optional[datetime] = None
    direccion: Optional[str] = None
    aforo_estimado: Optional[int] = None
    distrito: Optional[str] = None
    presupuesto_maximo: Optional[float] = None
    # ── Filtros opcionales del usuario ────────────────────────────────────
    filtro_proveedor_ids: List[int] = Field(default_factory=list)
    filtro_categoria_ids: List[int] = Field(default_factory=list)


class ChatRequest(BaseModel):
    mensaje: str
    historial: List[dict] = Field(default_factory=list)
    estado_conversacion: Optional[RecomendacionRequest] = None
    # ── Filtros opcionales del usuario (se copian al estado_conversacion) ──
    filtro_proveedor_ids: List[int] = Field(default_factory=list)
    filtro_categoria_ids: List[int] = Field(default_factory=list)


class GeminiRecomendacionSchema(BaseModel):
    """Esquema compatible con google-genai Structured Output.
    Idéntico a RecomendacionRequest pero con cantidades_servicios
    como list[CantidadServicio] en vez de dict[str, int]."""
    mensaje: str
    nombre_evento: Optional[str] = None
    tipo_evento: Optional[str] = None
    tematica_detectada: Optional[str] = None
    servicios_extra_detectados: list[str] = Field(default_factory=list)
    cantidades_servicios: list[CantidadServicio] = Field(default_factory=list)
    fecha_evento_inicio: Optional[datetime] = None
    fecha_evento_fin: Optional[datetime] = None
    direccion: Optional[str] = None
    aforo_estimado: Optional[int] = None
    distrito: Optional[str] = None
    presupuesto_maximo: Optional[float] = None

    def to_recomendacion_request(self) -> "RecomendacionRequest":
        """Convierte al modelo de dominio, transformando la lista a dict."""
        return RecomendacionRequest(
            mensaje=self.mensaje,
            nombre_evento=self.nombre_evento,
            tipo_evento=self.tipo_evento,
            tematica_detectada=self.tematica_detectada,
            servicios_extra_detectados=self.servicios_extra_detectados,
            cantidades_servicios={
                c.nombre_servicio: c.cantidad for c in self.cantidades_servicios
            },
            fecha_evento_inicio=self.fecha_evento_inicio,
            fecha_evento_fin=self.fecha_evento_fin,
            direccion=self.direccion,
            aforo_estimado=self.aforo_estimado,
            distrito=self.distrito,
            presupuesto_maximo=self.presupuesto_maximo,
        )



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
    estado_conversacion: Optional[RecomendacionRequest] = None
    resultados_principales: List[ProveedorRecomendado] = Field(default_factory=list)
    otras_opciones: List[ProveedorRecomendado] = Field(default_factory=list)

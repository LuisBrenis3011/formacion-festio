from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict

from app.domain.common.enums import EstadoBasico, TipoItemCatalogo


class CategoriaCreate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
    descripcion: Optional[str] = Field(None, max_length=500)


class CategoriaOut(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class TematicaCreate(BaseModel):
    categoria_id: int
    nombre: str = Field(..., min_length=2, max_length=100)
    imagen_referencial: Optional[str] = None


class TematicaOut(BaseModel):
    id: int
    categoria_id: int
    nombre: str
    imagen_referencial: Optional[str]

    model_config = ConfigDict(from_attributes=True)


# ── Servicios / Productos (Admin genérico) ────────────────────────────────────

class ServicioProductoCreate(BaseModel):
    proveedor_id: int
    categoria_id: int
    nombre: str = Field(..., min_length=2, max_length=200)
    tipo: TipoItemCatalogo
    requiere_persona: bool = False
    precio_unitario: float = Field(..., ge=0)
    stock_maximo_simultaneo: Optional[int] = Field(None, ge=0)
    duracion_base_horas: Optional[float] = Field(None, gt=0)


class ServicioProductoUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=200)
    precio_unitario: Optional[float] = Field(None, ge=0)
    stock_maximo_simultaneo: Optional[int] = Field(None, ge=0)
    duracion_base_horas: Optional[float] = Field(None, gt=0)
    estado: Optional[EstadoBasico] = None


class ServicioProductoOut(BaseModel):
    id: int
    proveedor_id: int
    categoria_id: int
    nombre: str
    tipo: TipoItemCatalogo
    requiere_persona: bool
    precio_unitario: float
    stock_maximo_simultaneo: Optional[int]
    duracion_base_horas: Optional[float]
    estado: EstadoBasico

    model_config = ConfigDict(from_attributes=True)


# ── Detalle Paquete ───────────────────────────────────────────────────────────

class DetallePaqueteCreate(BaseModel):
    servicio_producto_id: int
    cantidad_incluida: int = Field(1, gt=0)


class DetallePaqueteOut(BaseModel):
    id: int
    paquete_id: int
    servicio_producto_id: int
    cantidad_incluida: int
    servicio_nombre: Optional[str] = None  # para mostrar en frontend

    model_config = ConfigDict(from_attributes=True)


# ── Paquetes (Admin genérico) ─────────────────────────────────────────────────

class PaqueteCreate(BaseModel):
    proveedor_id: int
    categoria_id: int
    tematica_id: Optional[int] = None
    nombre: str = Field(..., min_length=2, max_length=200)
    descripcion: Optional[str] = Field(None, max_length=500)
    precio_base: float = Field(..., ge=0)
    detalles: List[DetallePaqueteCreate]


class PaqueteUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=200)
    descripcion: Optional[str] = Field(None, max_length=500)
    precio_base: Optional[float] = Field(None, ge=0)
    estado: Optional[EstadoBasico] = None


class PaqueteOut(BaseModel):
    id: int
    proveedor_id: int
    categoria_id: int
    tematica_id: Optional[int]
    nombre: str
    descripcion: Optional[str]
    precio_base: float
    estado: EstadoBasico
    detalles: List[DetallePaqueteOut]

    model_config = ConfigDict(from_attributes=True)


# ══════════════════════════════════════════════════════════════════════════════
# SCHEMAS B2B — Usados por los endpoints del proveedor autenticado
# El proveedor_id se inyecta desde el JWT, NO se envía en el body.
# ══════════════════════════════════════════════════════════════════════════════

class ProveedorServicioCreate(BaseModel):
    """Crear servicio/producto desde el panel del proveedor."""
    categoria_id: int
    nombre: str = Field(..., min_length=2, max_length=200)
    tipo: TipoItemCatalogo
    requiere_persona: bool = False
    precio_unitario: float = Field(..., ge=0)
    stock_maximo_simultaneo: int = Field(..., ge=0)  # OBLIGATORIO para B2B
    duracion_base_horas: Optional[float] = Field(None, gt=0)


class ProveedorServicioUpdate(BaseModel):
    """Actualizar servicio propio."""
    nombre: Optional[str] = Field(None, min_length=2, max_length=200)
    tipo: Optional[TipoItemCatalogo] = None
    requiere_persona: Optional[bool] = None
    precio_unitario: Optional[float] = Field(None, ge=0)
    stock_maximo_simultaneo: Optional[int] = Field(None, ge=0)
    duracion_base_horas: Optional[float] = Field(None, gt=0)
    estado: Optional[EstadoBasico] = None


class ProveedorPaqueteCreate(BaseModel):
    """Crear paquete desde el panel del proveedor."""
    categoria_id: int
    tematica_id: Optional[int] = None
    nombre: str = Field(..., min_length=2, max_length=200)
    descripcion: Optional[str] = Field(None, max_length=500)
    precio_base: float = Field(..., ge=0)
    detalles: List[DetallePaqueteCreate]


class ProveedorPaqueteUpdate(BaseModel):
    """Actualizar paquete propio."""
    categoria_id: Optional[int] = None
    tematica_id: Optional[int] = None
    nombre: Optional[str] = Field(None, min_length=2, max_length=200)
    descripcion: Optional[str] = Field(None, max_length=500)
    precio_base: Optional[float] = Field(None, ge=0)
    estado: Optional[EstadoBasico] = None
    detalles: Optional[List[DetallePaqueteCreate]] = None


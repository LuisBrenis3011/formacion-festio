from typing import List, Optional

from pydantic import BaseModel

from app.domain.common.enums import EstadoBasico, TipoItemCatalogo


class CategoriaCreate(BaseModel):
    nombre: str
    descripcion: Optional[str] = None


class CategoriaOut(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str]

    class Config:
        from_attributes = True


class TematicaCreate(BaseModel):
    categoria_id: int
    nombre: str
    imagen_referencial: Optional[str] = None


class TematicaOut(BaseModel):
    id: int
    categoria_id: int
    nombre: str
    imagen_referencial: Optional[str]

    class Config:
        from_attributes = True


# ── Servicios / Productos (Admin genérico) ────────────────────────────────────

class ServicioProductoCreate(BaseModel):
    proveedor_id: int
    categoria_id: int
    nombre: str
    tipo: TipoItemCatalogo
    requiere_persona: bool = False
    precio_unitario: float
    stock_maximo_simultaneo: Optional[int] = None
    duracion_base_horas: Optional[float] = None


class ServicioProductoUpdate(BaseModel):
    nombre: Optional[str] = None
    precio_unitario: Optional[float] = None
    stock_maximo_simultaneo: Optional[int] = None
    duracion_base_horas: Optional[float] = None
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

    class Config:
        from_attributes = True


# ── Detalle Paquete ───────────────────────────────────────────────────────────

class DetallePaqueteCreate(BaseModel):
    servicio_producto_id: int
    cantidad_incluida: int = 1


class DetallePaqueteOut(BaseModel):
    id: int
    paquete_id: int
    servicio_producto_id: int
    cantidad_incluida: int
    servicio_nombre: Optional[str] = None  # para mostrar en frontend

    class Config:
        from_attributes = True


# ── Paquetes (Admin genérico) ─────────────────────────────────────────────────

class PaqueteCreate(BaseModel):
    proveedor_id: int
    categoria_id: int
    tematica_id: Optional[int] = None
    nombre: str
    descripcion: Optional[str] = None
    precio_base: float
    detalles: List[DetallePaqueteCreate]


class PaqueteUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    precio_base: Optional[float] = None
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

    class Config:
        from_attributes = True


# ══════════════════════════════════════════════════════════════════════════════
# SCHEMAS B2B — Usados por los endpoints del proveedor autenticado
# El proveedor_id se inyecta desde el JWT, NO se envía en el body.
# ══════════════════════════════════════════════════════════════════════════════

class ProveedorServicioCreate(BaseModel):
    """Crear servicio/producto desde el panel del proveedor."""
    categoria_id: int
    nombre: str
    tipo: TipoItemCatalogo
    requiere_persona: bool = False
    precio_unitario: float
    stock_maximo_simultaneo: int  # OBLIGATORIO para B2B
    duracion_base_horas: Optional[float] = None


class ProveedorServicioUpdate(BaseModel):
    """Actualizar servicio propio."""
    nombre: Optional[str] = None
    tipo: Optional[TipoItemCatalogo] = None
    requiere_persona: Optional[bool] = None
    precio_unitario: Optional[float] = None
    stock_maximo_simultaneo: Optional[int] = None
    duracion_base_horas: Optional[float] = None
    estado: Optional[EstadoBasico] = None


class ProveedorPaqueteCreate(BaseModel):
    """Crear paquete desde el panel del proveedor."""
    categoria_id: int
    tematica_id: Optional[int] = None
    nombre: str
    descripcion: Optional[str] = None
    precio_base: float
    detalles: List[DetallePaqueteCreate]


class ProveedorPaqueteUpdate(BaseModel):
    """Actualizar paquete propio."""
    categoria_id: Optional[int] = None
    tematica_id: Optional[int] = None
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    precio_base: Optional[float] = None
    estado: Optional[EstadoBasico] = None
    detalles: Optional[List[DetallePaqueteCreate]] = None

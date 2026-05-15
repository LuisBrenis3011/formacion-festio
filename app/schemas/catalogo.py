from enum import Enum
from typing import List, Optional

from pydantic import BaseModel

from app.models.enums import EstadoBasico, TipoItemCatalogo


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


class DetallePaqueteCreate(BaseModel):
    servicio_producto_id: int
    cantidad_incluida: int = 1


class DetallePaqueteOut(BaseModel):
    id: int
    paquete_id: int
    servicio_producto_id: int
    cantidad_incluida: int

    class Config:
        from_attributes = True


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
    tematica_id: Optional[int] = None
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

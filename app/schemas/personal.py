from typing import List, Optional

from pydantic import BaseModel

from app.models.enums import EstadoBasico, RolPersonal


class PersonalRolCreate(BaseModel):
    rol: RolPersonal
    precio_por_rol: float
    rol_principal: bool = False


class PersonalRolOut(BaseModel):
    id: int
    rol: RolPersonal
    precio_por_rol: float
    rol_principal: bool

    class Config:
        from_attributes = True


class PersonalCreate(BaseModel):
    proveedor_id: int
    nombre: str
    telefono: Optional[str] = None
    roles: List[PersonalRolCreate]


class PersonalUpdate(BaseModel):
    nombre: Optional[str] = None
    telefono: Optional[str] = None
    estado: Optional[EstadoBasico] = None


class PersonalOut(BaseModel):
    id: int
    proveedor_id: int
    nombre: str
    telefono: Optional[str]
    estado: EstadoBasico
    roles: List[PersonalRolOut]

    class Config:
        from_attributes = True

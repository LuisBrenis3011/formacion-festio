from typing import List, Optional

from pydantic import BaseModel, Field

from app.domain.common.enums import EstadoBasico, RolPersonal


class PersonalRolCreate(BaseModel):
    rol: RolPersonal
    precio_por_rol: float = Field(..., ge=0)
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
    nombre: str = Field(..., min_length=2, max_length=100)
    telefono: Optional[str] = Field(None, max_length=20)
    roles: List[PersonalRolCreate]


class PersonalUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
    telefono: Optional[str] = Field(None, max_length=20)
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


from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from app.domain.common.enums import EstadoBasico, EstadoVerificacion, RolUsuario


# ── Validadores reutilizables ─────────────────────────────────────────────────

def _validar_no_vacio(v: str, campo: str) -> str:
    """Rechaza cadenas que sean solo espacios en blanco."""
    if not v or not v.strip():
        raise ValueError(f"{campo} no puede estar vacío")
    return v.strip()


def _validar_telefono(v: Optional[str]) -> Optional[str]:
    """Teléfono peruano: 9 dígitos, empieza con 9."""
    if v is None:
        return v
    v = v.strip()
    if v == "":
        return None
    import re
    if not re.match(r"^9\d{8}$", v):
        raise ValueError("El teléfono debe tener 9 dígitos y empezar con 9 (ej. 987654321)")
    return v


class UsuarioCreate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
    apellido: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    telefono: Optional[str] = None
    password: str = Field(..., min_length=8, max_length=128)
    rol: RolUsuario

    @field_validator("nombre", "apellido")
    @classmethod
    def nombre_no_vacio(cls, v: str, info) -> str:
        return _validar_no_vacio(v, info.field_name)

    @field_validator("telefono")
    @classmethod
    def telefono_valido(cls, v: Optional[str]) -> Optional[str]:
        return _validar_telefono(v)


class UsuarioOut(BaseModel):
    id: int
    nombre: str
    apellido: str
    email: EmailStr
    telefono: Optional[str]
    rol: RolUsuario
    estado: EstadoBasico
    fecha_registro: datetime

    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    rol: RolUsuario
    usuario_id: int
    nombre: str
    proveedor_id: Optional[int] = None


# ── Registro específico para Proveedor ────────────────────────────────────────

class RegistroProveedorRequest(BaseModel):
    """Registro de proveedor con datos de empresa incluidos."""
    nombre: str = Field(..., min_length=2, max_length=100)
    apellido: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    telefono: Optional[str] = None
    password: str = Field(..., min_length=8, max_length=128)
    nombre_empresa: str = Field(..., min_length=2, max_length=200)
    ruc: str = Field(..., pattern=r"^\d{11}$")
    distrito: str = Field(..., min_length=2, max_length=100)
    descripcion: Optional[str] = Field(None, max_length=500)
    capacidad_humana_total: Optional[int] = Field(0, ge=0)

    @field_validator("nombre", "apellido", "nombre_empresa", "distrito")
    @classmethod
    def textos_no_vacios(cls, v: str, info) -> str:
        return _validar_no_vacio(v, info.field_name)

    @field_validator("telefono")
    @classmethod
    def telefono_valido(cls, v: Optional[str]) -> Optional[str]:
        return _validar_telefono(v)


# ── Auth: endpoint /me ────────────────────────────────────────────────────────

class MeResponse(BaseModel):
    id: int
    nombre: str
    apellido: str
    email: str
    rol: RolUsuario
    estado: EstadoBasico
    proveedor_id: Optional[int] = None
    nombre_empresa: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ── Cliente ───────────────────────────────────────────────────────────────────

class ClienteCreate(BaseModel):
    usuario_id: int
    direccion: Optional[str] = Field(None, max_length=300)


class ClienteOut(BaseModel):
    id: int
    usuario_id: int
    direccion: Optional[str]

    model_config = ConfigDict(from_attributes=True)


# ── Proveedor ─────────────────────────────────────────────────────────────────

class ProveedorCreate(BaseModel):
    usuario_id: int
    nombre_empresa: str = Field(..., min_length=2, max_length=200)
    ruc: str = Field(..., pattern=r"^\d{11}$")
    descripcion: Optional[str] = Field(None, max_length=500)
    distrito: str = Field(..., min_length=2, max_length=100)
    capacidad_humana_total: Optional[int] = Field(0, ge=0)

    @field_validator("nombre_empresa", "distrito")
    @classmethod
    def textos_no_vacios(cls, v: str, info) -> str:
        return _validar_no_vacio(v, info.field_name)


class ProveedorUpdate(BaseModel):
    nombre_empresa: Optional[str] = Field(None, min_length=2, max_length=200)
    descripcion: Optional[str] = Field(None, max_length=500)
    distrito: Optional[str] = Field(None, min_length=2, max_length=100)
    capacidad_humana_total: Optional[int] = Field(None, ge=0)


class ProveedorOut(BaseModel):
    id: int
    usuario_id: int
    nombre_empresa: str
    ruc: str
    descripcion: Optional[str]
    distrito: str
    calificacion_promedio: float
    estado_verificacion: EstadoVerificacion
    capacidad_humana_total: int

    model_config = ConfigDict(from_attributes=True)


class ProveedorDashboardStats(BaseModel):
    total_servicios: int
    total_paquetes: int
    total_reservas: int

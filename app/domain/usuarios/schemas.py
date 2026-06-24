from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr

from app.domain.common.enums import EstadoBasico, EstadoVerificacion, RolUsuario


class UsuarioCreate(BaseModel):
    nombre: str
    apellido: str
    email: EmailStr
    telefono: Optional[str] = None
    password: str
    rol: RolUsuario


class UsuarioOut(BaseModel):
    id: int
    nombre: str
    apellido: str
    email: EmailStr
    telefono: Optional[str]
    rol: RolUsuario
    estado: EstadoBasico
    fecha_registro: datetime

    class Config:
        from_attributes = True


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
    nombre: str
    apellido: str
    email: EmailStr
    telefono: Optional[str] = None
    password: str
    nombre_empresa: str
    ruc: str
    distrito: str
    descripcion: Optional[str] = None
    capacidad_humana_total: Optional[int] = 0


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

    class Config:
        from_attributes = True


# ── Cliente ───────────────────────────────────────────────────────────────────

class ClienteCreate(BaseModel):
    usuario_id: int
    direccion: Optional[str] = None


class ClienteOut(BaseModel):
    id: int
    usuario_id: int
    direccion: Optional[str]

    class Config:
        from_attributes = True


# ── Proveedor ─────────────────────────────────────────────────────────────────

class ProveedorCreate(BaseModel):
    usuario_id: int
    nombre_empresa: str
    ruc: str
    descripcion: Optional[str] = None
    distrito: str
    capacidad_humana_total: Optional[int] = 0


class ProveedorUpdate(BaseModel):
    nombre_empresa: Optional[str] = None
    descripcion: Optional[str] = None
    distrito: Optional[str] = None
    capacidad_humana_total: Optional[int] = None


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

    class Config:
        from_attributes = True


class ProveedorDashboardStats(BaseModel):
    total_servicios: int
    total_paquetes: int
    total_reservas: int

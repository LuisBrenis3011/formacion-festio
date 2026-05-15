"""
Módulo 1 — USUARIOS
Tablas: Usuario, Cliente, Proveedor
"""
from sqlalchemy import (
    Column, Integer, String, Enum, TIMESTAMP, ForeignKey, DECIMAL, Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base
from app.models.enums import EstadoBasico, EstadoVerificacion, RolUsuario


class Usuario(Base):
    __tablename__ = "usuario"

    id              = Column(Integer, primary_key=True)
    nombre          = Column(String(100), nullable=False)
    apellido        = Column(String(100), nullable=False)
    email           = Column(String(150), unique=True, nullable=False)
    telefono        = Column(String(20))
    contrasena_hash = Column(String(255), nullable=False)
    rol             = Column(Enum(RolUsuario, name="tipo_rol_usuario"), nullable=False)
    fecha_registro  = Column(TIMESTAMP, server_default=func.now())
    updated_at      = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    estado          = Column(
        Enum(EstadoBasico, name="tipo_estado_basico"),
        nullable=False,
        default=EstadoBasico.ACTIVO,
        server_default="ACTIVO",
    )

    # ── Relaciones ────────────────────────────────────────────────────────────
    cliente        = relationship("Cliente",      back_populates="usuario", uselist=False)
    proveedor      = relationship("Proveedor",    back_populates="usuario", uselist=False)
    notificaciones = relationship("Notificacion", back_populates="usuario")


class Cliente(Base):
    __tablename__ = "cliente"

    id         = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey("usuario.id", ondelete="CASCADE"), unique=True, nullable=False)
    direccion  = Column(String(255))

    # ── Relaciones ────────────────────────────────────────────────────────────
    usuario = relationship("Usuario", back_populates="cliente")
    eventos = relationship("Evento",  back_populates="cliente")
    resenas = relationship("Resena",  back_populates="cliente")


class Proveedor(Base):
    __tablename__ = "proveedor"

    id                     = Column(Integer, primary_key=True)
    usuario_id             = Column(Integer, ForeignKey("usuario.id", ondelete="CASCADE"), unique=True, nullable=False)
    nombre_empresa         = Column(String(150), nullable=False)
    ruc                    = Column(String(20), unique=True, nullable=False)
    descripcion            = Column(Text)
    distrito               = Column(String(100), nullable=False)
    calificacion_promedio  = Column(DECIMAL(3, 2), default=0.00, server_default="0.00")
    estado_verificacion    = Column(
        Enum(EstadoVerificacion, name="tipo_estado_verificacion"),
        nullable=False,
        default=EstadoVerificacion.PENDIENTE,
        server_default="PENDIENTE",
    )
    capacidad_humana_total = Column(Integer, default=0, server_default="0")
    updated_at             = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # ── Relaciones ────────────────────────────────────────────────────────────
    usuario              = relationship("Usuario",                  back_populates="proveedor")
    personal             = relationship("Personal",                 back_populates="proveedor")
    servicios_productos  = relationship("ServicioProducto",         back_populates="proveedor")
    paquetes             = relationship("Paquete",                  back_populates="proveedor")
    reservas             = relationship("Reserva",                  back_populates="proveedor")
    resenas              = relationship("Resena",                   back_populates="proveedor")
    ocupaciones_globales = relationship("OcupacionGlobalProveedor", back_populates="proveedor")

"""
Módulo 3 — PERSONAL
Tablas: Personal, Personal_Rol
"""
from sqlalchemy import (
    Column, Integer, String, Enum, ForeignKey,
    Boolean, DECIMAL, UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.database import Base
from app.domain.common.enums import EstadoBasico, RolPersonal


class Personal(Base):
    __tablename__ = "personal"

    id           = Column(Integer, primary_key=True)
    proveedor_id = Column(Integer, ForeignKey("proveedor.id"), nullable=False)
    nombre       = Column(String(150), nullable=False)
    telefono     = Column(String(20))
    estado       = Column(
        Enum(EstadoBasico, name="tipo_estado_basico"),
        nullable=False,
        default=EstadoBasico.ACTIVO,
        server_default="ACTIVO",
    )

    # ── Relaciones ────────────────────────────────────────────────────────────
    proveedor        = relationship("Proveedor",               back_populates="personal")
    roles            = relationship("PersonalRol",             back_populates="personal",
                                    cascade="all, delete-orphan")
    detalles_reserva = relationship("DetalleReservaPersonal",  back_populates="personal")


class PersonalRol(Base):
    """
    Association Object: asigna uno o más roles a cada persona del proveedor.
    Constraint unique_personal_rol evita duplicar el mismo rol al mismo trabajador.
    """
    __tablename__ = "personal_rol"
    __table_args__ = (
        UniqueConstraint("personal_id", "rol", name="unique_personal_rol"),
    )

    id             = Column(Integer, primary_key=True)
    personal_id    = Column(Integer, ForeignKey("personal.id", ondelete="CASCADE"), nullable=False)
    rol            = Column(Enum(RolPersonal, name="tipo_rol_personal"), nullable=False)
    precio_por_rol = Column(DECIMAL(10, 2), nullable=False)
    rol_principal  = Column(Boolean, default=False, server_default="false")

    # ── Relaciones ────────────────────────────────────────────────────────────
    personal = relationship("Personal", back_populates="roles")

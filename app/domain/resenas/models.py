"""
Módulo 7a — RESEÑAS
Tabla: Resena
"""
from sqlalchemy import (
    Column, Integer, ForeignKey, Text, TIMESTAMP, CheckConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Resena(Base):
    __tablename__ = "resena"
    __table_args__ = (
        CheckConstraint("calificacion BETWEEN 1 AND 5", name="chk_calificacion_rango"),
    )

    id           = Column(Integer, primary_key=True)
    reserva_id   = Column(Integer, ForeignKey("reserva.id"), nullable=True)   # nullable para reseñas públicas
    cliente_id   = Column(Integer, ForeignKey("cliente.id"), nullable=True)   # nullable para reseñas públicas
    usuario_id   = Column(Integer, ForeignKey("usuario.id"), nullable=True)   # para reseñas públicas (usuario logueado)
    proveedor_id = Column(Integer, ForeignKey("proveedor.id"), nullable=False)
    calificacion = Column(Integer, nullable=False)
    comentario   = Column(Text)
    fecha        = Column(TIMESTAMP, server_default=func.now())

    # ── Relaciones ────────────────────────────────────────────────────────────
    reserva   = relationship("Reserva",   back_populates="resenas")
    cliente   = relationship("Cliente",   back_populates="resenas")
    usuario   = relationship("Usuario")
    proveedor = relationship("Proveedor", back_populates="resenas")

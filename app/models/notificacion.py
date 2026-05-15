"""
Módulo 7b — NOTIFICACIONES
Tabla: Notificacion
"""
from sqlalchemy import Column, Integer, ForeignKey, TIMESTAMP, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base
from app.models.enums import CanalNotificacion, EstadoNotificacion, TipoNotificacion


class Notificacion(Base):
    __tablename__ = "notificacion"

    id          = Column(Integer, primary_key=True)
    usuario_id  = Column(Integer, ForeignKey("usuario.id"), nullable=False)
    reserva_id  = Column(Integer, ForeignKey("reserva.id"), nullable=True)
    tipo        = Column(Enum(TipoNotificacion, name="tipo_notificacion_enum"), nullable=False)
    mensaje     = Column(Text, nullable=False)
    canal       = Column(Enum(CanalNotificacion, name="tipo_canal_notificacion"), nullable=False)
    estado      = Column(
        Enum(EstadoNotificacion, name="tipo_estado_notificacion"),
        nullable=False,
        default=EstadoNotificacion.ENVIADA,
        server_default="ENVIADA",
    )
    fecha_envio = Column(TIMESTAMP, server_default=func.now())

    # ── Relaciones ────────────────────────────────────────────────────────────
    usuario = relationship("Usuario", back_populates="notificaciones")
    reserva = relationship("Reserva", back_populates="notificaciones")

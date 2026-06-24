"""
Módulo 6 — PAGOS
Tablas: Pago_Transaccion, Comprobante
"""
from sqlalchemy import (
    Column, Integer, String, Enum, ForeignKey,
    DECIMAL, TIMESTAMP, CheckConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base
from app.domain.common.enums import EstadoPago, MetodoPago, TipoComprobante, TipoPago


class PagoTransaccion(Base):
    """
    Registra cada intento/resultado de pago.
    Association Object: tabla intermedia con columnas propias entre Reserva y Comprobante.
    """
    __tablename__ = "pago_transaccion"
    __table_args__ = (
        CheckConstraint("monto > 0", name="chk_monto_positivo"),
    )

    id                 = Column(Integer, primary_key=True)
    reserva_id         = Column(Integer, ForeignKey("reserva.id"), nullable=False)
    tipo_pago          = Column(Enum(TipoPago, name="tipo_pago_enum"), nullable=False)
    monto              = Column(DECIMAL(10, 2), nullable=False)
    metodo_pago        = Column(Enum(MetodoPago, name="tipo_metodo_pago"), nullable=False)
    estado             = Column(
        Enum(EstadoPago, name="tipo_estado_pago"),
        nullable=False,
        default=EstadoPago.PENDIENTE,
        server_default="PENDIENTE",
    )
    codigo_transaccion = Column(String(150))
    fecha_pago         = Column(TIMESTAMP, server_default=func.now())
    updated_at         = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # ── Relaciones ────────────────────────────────────────────────────────────
    reserva     = relationship("Reserva",     back_populates="pagos")
    comprobante = relationship("Comprobante", back_populates="pago", uselist=False)


class Comprobante(Base):
    """
    Documento fiscal emitido tras pago exitoso.
    El trigger trg_check_comprobante valida en BD que pago.reserva_id == self.reserva_id.
    """
    __tablename__ = "comprobante"

    id                 = Column(Integer, primary_key=True)
    reserva_id         = Column(Integer, ForeignKey("reserva.id"), nullable=False)
    pago_id            = Column(Integer, ForeignKey("pago_transaccion.id"), nullable=False)
    tipo               = Column(Enum(TipoComprobante, name="tipo_comprobante_enum"), nullable=False)
    numero_comprobante = Column(String(100), unique=True, nullable=False)
    fecha_emision      = Column(TIMESTAMP, server_default=func.now())
    url_pdf            = Column(String(255))

    # ── Relaciones ────────────────────────────────────────────────────────────
    reserva = relationship("Reserva",         back_populates="comprobantes")
    pago    = relationship("PagoTransaccion", back_populates="comprobante")

"""
Módulo 5 — RESERVAS
Tablas: Evento, Reserva, Detalle_Reserva, Detalle_Reserva_Personal
"""
from sqlalchemy import (
    Column, Integer, String, Enum, ForeignKey,
    DECIMAL, TIMESTAMP, CheckConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base
from app.models.enums import EstadoReserva


class Evento(Base):
    """
    Cabecera general del evento del cliente.
    Un evento puede tener reservas con múltiples proveedores.
    Ej: DJ de una empresa + decoración de otra.
    """
    __tablename__ = "evento"
    __table_args__ = (
        CheckConstraint("fecha_evento_fin > fecha_evento_inicio", name="chk_evento_rango"),
    )

    id                  = Column(Integer, primary_key=True)
    cliente_id          = Column(Integer, ForeignKey("cliente.id"), nullable=False)
    categoria_id        = Column(Integer, ForeignKey("categoria.id"), nullable=True)
    nombre_evento       = Column(String(150), nullable=False)
    tipo_evento         = Column(String(100))
    fecha_evento_inicio = Column(TIMESTAMP, nullable=False)
    fecha_evento_fin    = Column(TIMESTAMP, nullable=False)
    direccion           = Column(String(255), nullable=False)
    aforo_estimado      = Column(Integer)

    # ── Relaciones ────────────────────────────────────────────────────────────
    cliente   = relationship("Cliente",   back_populates="eventos")
    categoria = relationship("Categoria", back_populates="eventos")
    reservas  = relationship("Reserva",   back_populates="evento")


class Reserva(Base):
    """
    Una reserva por proveedor dentro de un evento.
    Maneja el ciclo de pago: 10 % adelanto online + 90 % en el local.
    Constraint contable: monto_total = monto_adelanto + monto_pendiente.
    """
    __tablename__ = "reserva"
    __table_args__ = (
        CheckConstraint(
            "monto_total = monto_adelanto + monto_pendiente",
            name="chk_montos_reserva",
        ),
    )

    id              = Column(Integer, primary_key=True)
    evento_id       = Column(Integer, ForeignKey("evento.id"), nullable=False)
    proveedor_id    = Column(Integer, ForeignKey("proveedor.id"), nullable=False)
    tematica_id     = Column(Integer, ForeignKey("tematica.id"), nullable=True)
    estado          = Column(
        Enum(EstadoReserva, name="tipo_estado_reserva"),
        nullable=False,
        default=EstadoReserva.PENDIENTE,
        server_default="PENDIENTE",
    )
    monto_total     = Column(DECIMAL(10, 2), nullable=False)
    costo_movilidad = Column(DECIMAL(10, 2), default=0.00, server_default="0.00")
    monto_adelanto  = Column(DECIMAL(10, 2), default=0.00, server_default="0.00")
    monto_pendiente = Column(DECIMAL(10, 2), nullable=False)
    fecha_creacion  = Column(TIMESTAMP, server_default=func.now())
    updated_at      = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    deleted_at      = Column(TIMESTAMP, nullable=True)

    # ── Relaciones ────────────────────────────────────────────────────────────
    evento         = relationship("Evento",          back_populates="reservas")
    proveedor      = relationship("Proveedor",       back_populates="reservas")
    tematica       = relationship("Tematica",        back_populates="reservas")
    detalles       = relationship("DetalleReserva",  back_populates="reserva",
                                  cascade="all, delete-orphan")
    pagos          = relationship("PagoTransaccion", back_populates="reserva")
    comprobantes   = relationship("Comprobante",     back_populates="reserva")
    resenas        = relationship("Resena",          back_populates="reserva")
    notificaciones = relationship("Notificacion",    back_populates="reserva")


class DetalleReserva(Base):
    """
    Cada línea de lo contratado en la reserva.
    Puede ser un paquete completo O un ítem suelto (nunca ambos a la vez).
    Association Object con columnas propias.
    """
    __tablename__ = "detalle_reserva"
    __table_args__ = (
        CheckConstraint("cantidad > 0", name="chk_cantidad_positiva"),
        CheckConstraint(
            "(paquete_id IS NOT NULL AND servicio_producto_id IS NULL) OR "
            "(paquete_id IS NULL AND servicio_producto_id IS NOT NULL)",
            name="chk_detalle_tipo",
        ),
    )

    id                         = Column(Integer, primary_key=True)
    reserva_id                 = Column(Integer, ForeignKey("reserva.id", ondelete="CASCADE"), nullable=False)
    paquete_id                 = Column(Integer, ForeignKey("paquete.id"), nullable=True)
    servicio_producto_id       = Column(Integer, ForeignKey("servicio_producto.id"), nullable=True)
    cantidad                   = Column(Integer, nullable=False)
    horas_contratadas          = Column(DECIMAL(5, 2))
    precio_unitario            = Column(DECIMAL(10, 2), nullable=False)
    subtotal                   = Column(DECIMAL(10, 2), nullable=False)
    fecha_hora_inicio_servicio = Column(TIMESTAMP)
    fecha_hora_fin_servicio    = Column(TIMESTAMP)
    deleted_at                 = Column(TIMESTAMP, nullable=True)

    # ── Relaciones ────────────────────────────────────────────────────────────
    reserva           = relationship("Reserva",          back_populates="detalles")
    paquete           = relationship("Paquete",          back_populates="detalles_reserva")
    servicio_producto = relationship("ServicioProducto", back_populates="detalles_reserva")
    personal_asignado = relationship("DetalleReservaPersonal", back_populates="detalle_reserva",
                                     cascade="all, delete-orphan")


class DetalleReservaPersonal(Base):
    """
    Asigna personas físicas específicas a una línea de la reserva.
    Resuelve el problema de multi-rol:
    si Juan (DJ y Bailarín) está asignado aquí, queda bloqueado para otros eventos.
    Association Object con columnas propias.
    """
    __tablename__ = "detalle_reserva_personal"

    id                 = Column(Integer, primary_key=True)
    detalle_reserva_id = Column(Integer, ForeignKey("detalle_reserva.id", ondelete="CASCADE"), nullable=False)
    personal_id        = Column(Integer, ForeignKey("personal.id"), nullable=False)
    fecha_asignacion   = Column(TIMESTAMP, nullable=False)
    deleted_at         = Column(TIMESTAMP, nullable=True)

    # ── Relaciones ────────────────────────────────────────────────────────────
    detalle_reserva = relationship("DetalleReserva", back_populates="personal_asignado")
    personal        = relationship("Personal",       back_populates="detalles_reserva")

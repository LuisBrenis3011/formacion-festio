"""
Módulo 4 — OCUPACIÓN (Disponibilidad)
Tablas: Ocupacion_Global_Proveedor, Ocupacion_Servicio_Producto
"""
from sqlalchemy import (
    Column, Integer, ForeignKey, TIMESTAMP, CheckConstraint,
)
from sqlalchemy.orm import relationship

from app.database import Base


class OcupacionGlobalProveedor(Base):
    """
    Controla el límite físico total del proveedor en un rango horario.
    Si un proveedor tiene capacidad_humana_total = 12 personas,
    esta tabla garantiza que nunca se supere ese límite.
    """
    __tablename__ = "ocupacion_global_proveedor"
    __table_args__ = (
        CheckConstraint("fecha_hora_fin > fecha_hora_inicio", name="chk_ocupacion_global_rango"),
    )

    id                      = Column(Integer, primary_key=True)
    proveedor_id            = Column(Integer, ForeignKey("proveedor.id"), nullable=False)
    fecha_hora_inicio       = Column(TIMESTAMP, nullable=False)
    fecha_hora_fin          = Column(TIMESTAMP, nullable=False)
    total_personas_ocupadas = Column(Integer, nullable=False)

    # ── Relaciones ────────────────────────────────────────────────────────────
    proveedor = relationship("Proveedor", back_populates="ocupaciones_globales")


class OcupacionServicioProducto(Base):
    """
    Controla cuántas unidades de un ítem específico están en uso
    en un rango horario determinado.
    Ej: De 6 DJs disponibles, 4 ya están ocupados el sábado de 3pm a 8pm.
    """
    __tablename__ = "ocupacion_servicio_producto"
    __table_args__ = (
        CheckConstraint("fecha_hora_fin > fecha_hora_inicio", name="chk_ocupacion_servicio_rango"),
    )

    id                   = Column(Integer, primary_key=True)
    servicio_producto_id = Column(Integer, ForeignKey("servicio_producto.id"), nullable=False)
    fecha_hora_inicio    = Column(TIMESTAMP, nullable=False)
    fecha_hora_fin       = Column(TIMESTAMP, nullable=False)
    cantidad_ocupada     = Column(Integer, nullable=False)

    # ── Relaciones ────────────────────────────────────────────────────────────
    servicio_producto = relationship("ServicioProducto", back_populates="ocupaciones")

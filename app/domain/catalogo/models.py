"""
Módulo 2 — CATÁLOGO
Tablas: Categoria, Tematica, Servicio_Producto, Paquete, Detalle_Paquete
"""
from sqlalchemy import (
    Column, Integer, String, Enum, ForeignKey,
    Boolean, DECIMAL, TIMESTAMP, Text, CheckConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base
from app.domain.common.enums import EstadoBasico, TipoItemCatalogo


class Categoria(Base):
    __tablename__ = "categoria"

    id          = Column(Integer, primary_key=True)
    nombre      = Column(String(150), nullable=False)
    descripcion = Column(Text)

    # ── Relaciones ────────────────────────────────────────────────────────────
    tematicas           = relationship("Tematica",         back_populates="categoria")
    servicios_productos = relationship("ServicioProducto", back_populates="categoria")
    paquetes            = relationship("Paquete",          back_populates="categoria")
    eventos             = relationship("Evento",           back_populates="categoria")


class Tematica(Base):
    """Temáticas específicas dentro de una categoría (Spiderman, Frozen, etc.)"""
    __tablename__ = "tematica"

    id                 = Column(Integer, primary_key=True)
    categoria_id       = Column(Integer, ForeignKey("categoria.id"), nullable=False)
    nombre             = Column(String(150), nullable=False)
    imagen_referencial = Column(String(255))

    # ── Relaciones ────────────────────────────────────────────────────────────
    categoria = relationship("Categoria", back_populates="tematicas")
    paquetes  = relationship("Paquete",   back_populates="tematica")
    reservas  = relationship("Reserva",   back_populates="tematica")


class ServicioProducto(Base):
    """
    Unidad mínima del catálogo.
    Puede ser un servicio humano (DJ, bailarín) o un producto físico (toldo, sillas).
    """
    __tablename__ = "servicio_producto"

    id                      = Column(Integer, primary_key=True)
    proveedor_id            = Column(Integer, ForeignKey("proveedor.id"), nullable=False)
    categoria_id            = Column(Integer, ForeignKey("categoria.id"), nullable=False)
    nombre                  = Column(String(150), nullable=False)
    tipo                    = Column(
        Enum(TipoItemCatalogo, name="tipo_item_catalogo"), nullable=False,
    )
    requiere_persona        = Column(Boolean, default=False, server_default="false")
    precio_unitario         = Column(DECIMAL(10, 2), nullable=False)
    stock_maximo_simultaneo = Column(Integer)
    duracion_base_horas     = Column(DECIMAL(5, 2))
    estado                  = Column(
        Enum(EstadoBasico, name="tipo_estado_basico"),
        nullable=False,
        default=EstadoBasico.ACTIVO,
        server_default="ACTIVO",
    )
    updated_at              = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    deleted_at              = Column(TIMESTAMP, nullable=True)

    # ── Relaciones ────────────────────────────────────────────────────────────
    proveedor        = relationship("Proveedor",                  back_populates="servicios_productos")
    categoria        = relationship("Categoria",                  back_populates="servicios_productos")
    detalles_paquete = relationship("DetallePaquete",             back_populates="servicio_producto")
    ocupaciones      = relationship("OcupacionServicioProducto",  back_populates="servicio_producto")
    detalles_reserva = relationship("DetalleReserva",             back_populates="servicio_producto")


class Paquete(Base):
    """
    Agrupación de servicios/productos ofrecida por un proveedor.
    Ej: 'Show Infantil Básico' = 1 animador + 1 DJ + 1 bailarín
    """
    __tablename__ = "paquete"

    id           = Column(Integer, primary_key=True)
    proveedor_id = Column(Integer, ForeignKey("proveedor.id"), nullable=False)
    categoria_id = Column(Integer, ForeignKey("categoria.id"), nullable=False)
    tematica_id  = Column(Integer, ForeignKey("tematica.id"), nullable=True)
    nombre       = Column(String(150), nullable=False)
    descripcion  = Column(Text)
    precio_base  = Column(DECIMAL(10, 2), nullable=False)
    estado       = Column(
        Enum(EstadoBasico, name="tipo_estado_basico"),
        nullable=False,
        default=EstadoBasico.ACTIVO,
        server_default="ACTIVO",
    )
    updated_at   = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # ── Relaciones ────────────────────────────────────────────────────────────
    proveedor        = relationship("Proveedor",      back_populates="paquetes")
    categoria        = relationship("Categoria",      back_populates="paquetes")
    tematica         = relationship("Tematica",       back_populates="paquetes")
    detalles         = relationship("DetallePaquete", back_populates="paquete", cascade="all, delete-orphan")
    detalles_reserva = relationship("DetalleReserva", back_populates="paquete")


class DetallePaquete(Base):
    """
    Composición de un paquete: qué servicios/productos incluye y en qué cantidad.
    Association Object: tabla intermedia con columnas propias.
    """
    __tablename__ = "detalle_paquete"
    __table_args__ = (
        CheckConstraint("cantidad_incluida > 0", name="chk_cantidad_incluida_positiva"),
    )

    id                   = Column(Integer, primary_key=True)
    paquete_id           = Column(Integer, ForeignKey("paquete.id", ondelete="CASCADE"), nullable=False)
    servicio_producto_id = Column(Integer, ForeignKey("servicio_producto.id"), nullable=False)
    cantidad_incluida    = Column(Integer, nullable=False)

    # ── Relaciones ────────────────────────────────────────────────────────────
    paquete           = relationship("Paquete",          back_populates="detalles")
    servicio_producto = relationship("ServicioProducto", back_populates="detalles_paquete")

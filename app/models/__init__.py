# Importar todos los modelos para que SQLAlchemy y Alembic
# los detecten automáticamente al generar las migraciones.

from app.models.enums import (  # noqa: F401
    RolUsuario, EstadoBasico, EstadoVerificacion,
    TipoItemCatalogo, RolPersonal, EstadoReserva,
    TipoPago, MetodoPago, EstadoPago, TipoComprobante,
    TipoNotificacion, CanalNotificacion, EstadoNotificacion,
)

from app.models.usuario        import Usuario, Cliente, Proveedor
from app.models.personal       import Personal, PersonalRol
from app.models.catalogo       import Categoria, Tematica, ServicioProducto, Paquete, DetallePaquete
from app.models.disponibilidad import OcupacionGlobalProveedor, OcupacionServicioProducto
from app.models.reserva        import Evento, Reserva, DetalleReserva, DetalleReservaPersonal
from app.models.pago           import PagoTransaccion, Comprobante
from app.models.resena         import Resena
from app.models.notificacion   import Notificacion

__all__ = [
    # Enums
    "RolUsuario", "EstadoBasico", "EstadoVerificacion",
    "TipoItemCatalogo", "RolPersonal", "EstadoReserva",
    "TipoPago", "MetodoPago", "EstadoPago", "TipoComprobante",
    "TipoNotificacion", "CanalNotificacion", "EstadoNotificacion",
    # Modelos (20 tablas)
    "Usuario", "Cliente", "Proveedor",
    "Personal", "PersonalRol",
    "Categoria", "Tematica", "ServicioProducto", "Paquete", "DetallePaquete",
    "OcupacionGlobalProveedor", "OcupacionServicioProducto",
    "Evento", "Reserva", "DetalleReserva", "DetalleReservaPersonal",
    "PagoTransaccion", "Comprobante",
    "Resena",
    "Notificacion",
]

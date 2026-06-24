# Importar todos los modelos para que SQLAlchemy y Alembic
# los detecten automáticamente al generar las migraciones.

from app.domain.common.enums import (  # noqa: F401
    RolUsuario, EstadoBasico, EstadoVerificacion,
    TipoItemCatalogo, RolPersonal, EstadoReserva,
    TipoPago, MetodoPago, EstadoPago, TipoComprobante,
    TipoNotificacion, CanalNotificacion, EstadoNotificacion,
)

from app.domain.usuarios.models        import Usuario, Cliente, Proveedor
from app.domain.personal.models       import Personal, PersonalRol
from app.domain.catalogo.models       import Categoria, Tematica, ServicioProducto, Paquete, DetallePaquete
from app.domain.disponibilidad.models import OcupacionGlobalProveedor, OcupacionServicioProducto
from app.domain.reservas.models        import Evento, Reserva, DetalleReserva, DetalleReservaPersonal
from app.domain.pagos.models           import PagoTransaccion, Comprobante
from app.domain.resenas.models         import Resena
from app.domain.notificaciones.models   import Notificacion

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

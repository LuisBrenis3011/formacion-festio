"""
Enums nativos de PostgreSQL mapeados a Python.
Cada nombre de enum aquí coincide con el CREATE TYPE del SQL.

Convención: el parámetro `name=` de Column(Enum(...)) en los modelos
debe coincidir EXACTAMENTE con el nombre del tipo en PostgreSQL.
"""
import enum


# ── Módulo 1: Usuarios ───────────────────────────────────────────────────────

class RolUsuario(str, enum.Enum):
    """CREATE TYPE tipo_rol_usuario"""
    CLIENTE   = "CLIENTE"
    PROVEEDOR = "PROVEEDOR"
    ADMIN     = "ADMIN"


class EstadoBasico(str, enum.Enum):
    """CREATE TYPE tipo_estado_basico"""
    ACTIVO   = "ACTIVO"
    INACTIVO = "INACTIVO"


class EstadoVerificacion(str, enum.Enum):
    """CREATE TYPE tipo_estado_verificacion"""
    PENDIENTE  = "PENDIENTE"
    VERIFICADO = "VERIFICADO"
    SUSPENDIDO = "SUSPENDIDO"


# ── Módulo 2: Catálogo ───────────────────────────────────────────────────────

class TipoItemCatalogo(str, enum.Enum):
    """CREATE TYPE tipo_item_catalogo"""
    SERVICIO = "SERVICIO"
    PRODUCTO = "PRODUCTO"


# ── Módulo 3: Personal ──────────────────────────────────────────────────────

class RolPersonal(str, enum.Enum):
    """CREATE TYPE tipo_rol_personal"""
    DJ                  = "DJ"
    ANIMADOR            = "ANIMADOR"
    BAILARIN            = "BAILARIN"
    PAYASO              = "PAYASO"
    MUÑECO              = "MUÑECO"
    MESERO              = "MESERO"
    MAESTRO_DE_CEREMONIA = "MAESTRO_DE_CEREMONIA"


# ── Módulo 5: Reservas ──────────────────────────────────────────────────────

class EstadoReserva(str, enum.Enum):
    """CREATE TYPE tipo_estado_reserva"""
    PENDIENTE  = "PENDIENTE"
    CONFIRMADA = "CONFIRMADA"
    COMPLETADA = "COMPLETADA"
    CANCELADA  = "CANCELADA"


# ── Módulo 6: Pagos ─────────────────────────────────────────────────────────

class TipoPago(str, enum.Enum):
    """CREATE TYPE tipo_pago_enum"""
    ADELANTO_ONLINE  = "ADELANTO_ONLINE"
    SALDO_PRESENCIAL = "SALDO_PRESENCIAL"


class MetodoPago(str, enum.Enum):
    """CREATE TYPE tipo_metodo_pago"""
    TARJETA  = "TARJETA"
    YAPE     = "YAPE"
    PLIN     = "PLIN"
    EFECTIVO = "EFECTIVO"


class EstadoPago(str, enum.Enum):
    """CREATE TYPE tipo_estado_pago"""
    PENDIENTE = "PENDIENTE"
    APROBADO  = "APROBADO"
    RECHAZADO = "RECHAZADO"


class TipoComprobante(str, enum.Enum):
    """CREATE TYPE tipo_comprobante_enum"""
    BOLETA  = "BOLETA"
    FACTURA = "FACTURA"


# ── Módulo 7: Notificaciones ────────────────────────────────────────────────

class TipoNotificacion(str, enum.Enum):
    """CREATE TYPE tipo_notificacion_enum"""
    CONFIRMACION        = "CONFIRMACION"
    SOLICITUD_SOBRECUPO = "SOLICITUD_SOBRECUPO"
    RECORDATORIO        = "RECORDATORIO"


class CanalNotificacion(str, enum.Enum):
    """CREATE TYPE tipo_canal_notificacion"""
    EMAIL = "EMAIL"
    PUSH  = "PUSH"
    SMS   = "SMS"


class EstadoNotificacion(str, enum.Enum):
    """CREATE TYPE tipo_estado_notificacion"""
    ENVIADA = "ENVIADA"
    LEIDA   = "LEIDA"
    FALLIDA = "FALLIDA"

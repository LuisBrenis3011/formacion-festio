# ── Servicios de lógica de negocio ────────────────────────────────────────────
# Cada módulo contiene la lógica de BD y validaciones para su entidad.
# Los routers importan estos módulos directamente:
#     from app.services import cliente_service
#     ...

from app.services import (  # noqa: F401
    auth_service,
    bloqueo_service,
    catalogo_service,
    cliente_service,
    disponibilidad_service,
    ia_service,
    notificacion_service,
    pago_service,
    paquete_service,
    personal_service,
    proveedor_inventario_service,
    proveedor_paquete_service,
    proveedor_service,
    recomendacion_service,
    resena_service,
    usuario_service,
)

from typing import List, Optional

from fastapi import HTTPException

from app.domain.catalogo.models import Paquete, ServicioProducto
from app.domain.common.enums import EstadoBasico, EstadoVerificacion
from app.domain.reservas.models import Reserva
from app.domain.usuarios.models import Proveedor, Usuario
from app.domain.usuarios.schemas import ProveedorCreate, ProveedorUpdate, ProveedorDashboardStats

from app.repositories.usuario_repository import ProveedorRepository
from app.repositories.catalogo_repository import ServicioProductoRepository, PaqueteRepository
from app.repositories.reserva_repository import ReservaRepository


def listar_proveedores(distrito: Optional[str], repo: ProveedorRepository, skip: int = 0, limit: int = 100) -> List[Proveedor]:
    query = repo.db.query(Proveedor).filter(
        Proveedor.estado_verificacion == EstadoVerificacion.VERIFICADO
    )
    if distrito:
        query = query.filter(Proveedor.distrito.ilike(f"%{distrito}%"))
    return query.offset(skip).limit(limit).all()


def obtener_proveedor(proveedor_id: int, repo: ProveedorRepository) -> Proveedor:
    """Busca un proveedor por ID. Lanza 404 si no existe."""
    proveedor = repo.get(proveedor_id)
    if not proveedor:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    return proveedor


def crear_proveedor(datos: ProveedorCreate, repo: ProveedorRepository) -> Proveedor:
    """Crea un nuevo proveedor a partir de los datos validados."""
    return repo.create(datos)


def actualizar_proveedor(
    proveedor_id: int, datos: ProveedorUpdate, repo: ProveedorRepository
) -> Proveedor:
    """Actualiza los campos enviados del proveedor. Lanza 404 si no existe."""
    proveedor = repo.update(proveedor_id, datos)
    if not proveedor:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    return proveedor


# ── Endpoints del proveedor autenticado ───────────────────────────────────────

def obtener_mi_perfil(usuario: Usuario, repo: ProveedorRepository) -> Proveedor:
    """Obtiene el perfil del proveedor logueado."""
    proveedor = repo.db.query(Proveedor).filter(
        Proveedor.usuario_id == usuario.id
    ).first()
    if not proveedor:
        raise HTTPException(status_code=404, detail="Perfil de proveedor no encontrado")
    return proveedor


def actualizar_mi_perfil(
    usuario: Usuario, datos: ProveedorUpdate, repo: ProveedorRepository
) -> Proveedor:
    """Actualiza el perfil propio del proveedor."""
    proveedor = obtener_mi_perfil(usuario, repo)

    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(proveedor, campo, valor)

    repo.db.commit()
    repo.db.refresh(proveedor)
    return proveedor


def obtener_dashboard_stats(
    proveedor: Proveedor,
    servicio_repo: ServicioProductoRepository,
    paquete_repo: PaqueteRepository,
    reserva_repo: ReservaRepository
) -> ProveedorDashboardStats:
    """Estadísticas del proveedor para el dashboard."""
    total_servicios = servicio_repo.db.query(ServicioProducto).filter(
        ServicioProducto.proveedor_id == proveedor.id,
        ServicioProducto.deleted_at == None,
    ).count()

    total_paquetes = paquete_repo.db.query(Paquete).filter(
        Paquete.proveedor_id == proveedor.id,
        Paquete.estado == EstadoBasico.ACTIVO,
    ).count()

    total_reservas = reserva_repo.db.query(Reserva).filter(
        Reserva.proveedor_id == proveedor.id,
    ).count()

    return ProveedorDashboardStats(
        total_servicios=total_servicios,
        total_paquetes=total_paquetes,
        total_reservas=total_reservas,
    )

from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.domain.catalogo.models import Paquete, ServicioProducto
from app.domain.common.enums import EstadoBasico, EstadoVerificacion
from app.domain.resenas.models import Resena
from app.domain.resenas.schemas import MarketAnalyticsOut
from app.domain.reservas.models import Reserva, DetalleReserva
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


def obtener_market_analytics(proveedor: Proveedor, db: Session) -> MarketAnalyticsOut:
    """Estadísticas de mercado del proveedor: reseñas, top paquetes, reseñas recientes."""

    stats = db.query(
        func.coalesce(func.avg(Resena.calificacion), 0).label("promedio"),
        func.count(Resena.id).label("total"),
    ).filter(
        Resena.proveedor_id == proveedor.id,
    ).first()

    calificacion_promedio = round(float(stats.promedio), 2)
    total_resenas = stats.total

    distribucion_rows = db.query(
        Resena.calificacion,
        func.count(Resena.id).label("conteo"),
    ).filter(
        Resena.proveedor_id == proveedor.id,
    ).group_by(Resena.calificacion).all()

    distribucion_estrellas: dict[int, int] = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for row in distribucion_rows:
        distribucion_estrellas[row.calificacion] = row.conteo

    top_rows = db.query(
        DetalleReserva.paquete_id,
        Paquete.nombre,
        func.count(DetalleReserva.id).label("ventas"),
    ).join(
        Reserva, DetalleReserva.reserva_id == Reserva.id,
    ).join(
        Paquete, DetalleReserva.paquete_id == Paquete.id,
    ).filter(
        Reserva.proveedor_id == proveedor.id,
        DetalleReserva.paquete_id.isnot(None),
        DetalleReserva.deleted_at.is_(None),
        Reserva.deleted_at.is_(None),
    ).group_by(
        DetalleReserva.paquete_id, Paquete.nombre,
    ).order_by(
        func.count(DetalleReserva.id).desc(),
    ).limit(3).all()

    max_ventas = top_rows[0].ventas if top_rows else 1
    top_paquetes = [
        {
            "paquete_id": row.paquete_id,
            "nombre": row.nombre,
            "ventas": row.ventas,
            "porcentaje": round((row.ventas / max_ventas) * 100) if max_ventas > 0 else 0,
        }
        for row in top_rows
    ]

    resenas_rows = db.query(
        Resena.id,
        Usuario.nombre.label("cliente_nombre"),
        Resena.calificacion,
        Resena.comentario,
        Resena.fecha,
    ).outerjoin(
        Usuario, Resena.usuario_id == Usuario.id,
    ).filter(
        Resena.proveedor_id == proveedor.id,
        Resena.fecha.isnot(None),
    ).order_by(
        Resena.fecha.desc(),
    ).limit(6).all()

    resenas_recientes = [
        {
            "id": row.id,
            "cliente_nombre": row.cliente_nombre or "Anónimo",
            "calificacion": row.calificacion,
            "comentario": row.comentario,
            "fecha": row.fecha.isoformat(),
        }
        for row in resenas_rows
    ]

    return MarketAnalyticsOut(
        calificacion_promedio=calificacion_promedio,
        total_resenas=total_resenas,
        distribucion_estrellas=distribucion_estrellas,
        top_paquetes=top_paquetes,
        resenas_recientes=resenas_recientes,
    )

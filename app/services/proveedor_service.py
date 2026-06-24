from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.domain.catalogo.models import Paquete, ServicioProducto
from app.domain.common.enums import EstadoBasico, EstadoVerificacion
from app.domain.reservas.models import Reserva
from app.domain.usuarios.models import Proveedor, Usuario
from app.domain.usuarios.schemas import ProveedorCreate, ProveedorUpdate, ProveedorDashboardStats


def listar_proveedores(distrito: Optional[str], db: Session) -> List[Proveedor]:
    """Lista proveedores verificados. Filtra por distrito si se indica."""
    query = db.query(Proveedor).filter(
        Proveedor.estado_verificacion == EstadoVerificacion.VERIFICADO
    )
    if distrito:
        query = query.filter(Proveedor.distrito.ilike(f"%{distrito}%"))
    return query.all()


def obtener_proveedor(proveedor_id: int, db: Session) -> Proveedor:
    """Busca un proveedor por ID. Lanza 404 si no existe."""
    proveedor = db.query(Proveedor).filter(Proveedor.id == proveedor_id).first()
    if not proveedor:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    return proveedor


def crear_proveedor(datos: ProveedorCreate, db: Session) -> Proveedor:
    """Crea un nuevo proveedor a partir de los datos validados."""
    proveedor = Proveedor(**datos.model_dump())
    db.add(proveedor)
    db.commit()
    db.refresh(proveedor)
    return proveedor


def actualizar_proveedor(
    proveedor_id: int, datos: ProveedorUpdate, db: Session
) -> Proveedor:
    """Actualiza los campos enviados del proveedor. Lanza 404 si no existe."""
    proveedor = db.query(Proveedor).filter(Proveedor.id == proveedor_id).first()
    if not proveedor:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")

    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(proveedor, campo, valor)

    db.commit()
    db.refresh(proveedor)
    return proveedor


# ── Endpoints del proveedor autenticado ───────────────────────────────────────

def obtener_mi_perfil(usuario: Usuario, db: Session) -> Proveedor:
    """Obtiene el perfil del proveedor logueado."""
    proveedor = db.query(Proveedor).filter(
        Proveedor.usuario_id == usuario.id
    ).first()
    if not proveedor:
        raise HTTPException(status_code=404, detail="Perfil de proveedor no encontrado")
    return proveedor


def actualizar_mi_perfil(
    usuario: Usuario, datos: ProveedorUpdate, db: Session
) -> Proveedor:
    """Actualiza el perfil propio del proveedor."""
    proveedor = obtener_mi_perfil(usuario, db)

    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(proveedor, campo, valor)

    db.commit()
    db.refresh(proveedor)
    return proveedor


def obtener_dashboard_stats(proveedor: Proveedor, db: Session) -> ProveedorDashboardStats:
    """Estadísticas del proveedor para el dashboard."""
    total_servicios = db.query(ServicioProducto).filter(
        ServicioProducto.proveedor_id == proveedor.id,
        ServicioProducto.deleted_at == None,
    ).count()

    total_paquetes = db.query(Paquete).filter(
        Paquete.proveedor_id == proveedor.id,
        Paquete.estado == EstadoBasico.ACTIVO,
    ).count()

    total_reservas = db.query(Reserva).filter(
        Reserva.proveedor_id == proveedor.id,
    ).count()

    return ProveedorDashboardStats(
        total_servicios=total_servicios,
        total_paquetes=total_paquetes,
        total_reservas=total_reservas,
    )

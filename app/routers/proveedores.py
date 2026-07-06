from typing import List, Optional

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_current_user, get_current_proveedor
from app.domain.usuarios.models import Proveedor, Usuario
from app.domain.usuarios.schemas import (
    ProveedorCreate, ProveedorUpdate, ProveedorOut, ProveedorDashboardStats,
)
from app.repositories.usuario_repository import ProveedorRepository, get_proveedor_repo
from app.repositories.catalogo_repository import ServicioProductoRepository, PaqueteRepository, get_servicio_producto_repo, get_paquete_repo
from app.repositories.reserva_repository import ReservaRepository, get_reserva_repo
from app.services import proveedor_service

router = APIRouter()


@router.get("/", response_model=List[ProveedorOut])
def listar_proveedores(
    distrito: Optional[str] = Query(None, description="Filtrar por distrito"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    repo: ProveedorRepository = Depends(get_proveedor_repo),
):
    return proveedor_service.listar_proveedores(distrito, repo, skip=skip, limit=limit)


@router.get("/mi-perfil", response_model=ProveedorOut)
def mi_perfil(
    usuario: Usuario = Depends(get_current_user),
    repo: ProveedorRepository = Depends(get_proveedor_repo),
):
    """Obtiene el perfil del proveedor logueado."""
    return proveedor_service.obtener_mi_perfil(usuario, repo)


@router.patch("/mi-perfil", response_model=ProveedorOut)
def actualizar_mi_perfil(
    datos: ProveedorUpdate,
    usuario: Usuario = Depends(get_current_user),
    repo: ProveedorRepository = Depends(get_proveedor_repo),
):
    """Actualiza el perfil propio del proveedor."""
    return proveedor_service.actualizar_mi_perfil(usuario, datos, repo)


@router.get("/mi-dashboard", response_model=ProveedorDashboardStats)
def dashboard_stats(
    proveedor: Proveedor = Depends(get_current_proveedor),
    servicio_repo: ServicioProductoRepository = Depends(get_servicio_producto_repo),
    paquete_repo: PaqueteRepository = Depends(get_paquete_repo),
    reserva_repo: ReservaRepository = Depends(get_reserva_repo),
):
    """Estadísticas del proveedor para su dashboard."""
    return proveedor_service.obtener_dashboard_stats(proveedor, servicio_repo, paquete_repo, reserva_repo)


@router.get("/{proveedor_id}", response_model=ProveedorOut)
def obtener_proveedor(proveedor_id: int, repo: ProveedorRepository = Depends(get_proveedor_repo)):
    return proveedor_service.obtener_proveedor(proveedor_id, repo)


@router.post("/", response_model=ProveedorOut, status_code=201)
def crear_proveedor(
    datos: ProveedorCreate,
    repo: ProveedorRepository = Depends(get_proveedor_repo),
    _: Usuario = Depends(get_current_user)
):
    return proveedor_service.crear_proveedor(datos, repo)


@router.patch("/{proveedor_id}", response_model=ProveedorOut)
def actualizar_proveedor(
    proveedor_id: int,
    datos: ProveedorUpdate,
    repo: ProveedorRepository = Depends(get_proveedor_repo),
    _: Usuario = Depends(get_current_user)
):
    """Endpoints administrativos."""
    return proveedor_service.actualizar_proveedor(proveedor_id, datos, repo)
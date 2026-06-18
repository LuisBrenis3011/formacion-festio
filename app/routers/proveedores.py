from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_current_proveedor
from app.database import get_db
from app.models.usuario import Usuario, Proveedor
from app.schemas.usuario import (
    ProveedorCreate, ProveedorUpdate, ProveedorOut, ProveedorDashboardStats,
)
from app.services import proveedor_service

router = APIRouter()


@router.get("/", response_model=List[ProveedorOut])
def listar_proveedores(
    distrito: str = None,
    db: Session = Depends(get_db)
):
    """Lista todos los proveedores verificados. Filtra por distrito si se indica."""
    return proveedor_service.listar_proveedores(distrito, db)


@router.get("/mi-perfil", response_model=ProveedorOut)
def mi_perfil(
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Obtiene el perfil del proveedor logueado."""
    return proveedor_service.obtener_mi_perfil(usuario, db)


@router.patch("/mi-perfil", response_model=ProveedorOut)
def actualizar_mi_perfil(
    datos: ProveedorUpdate,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Actualiza el perfil propio del proveedor."""
    return proveedor_service.actualizar_mi_perfil(usuario, datos, db)


@router.get("/mi-dashboard", response_model=ProveedorDashboardStats)
def mi_dashboard(
    proveedor: Proveedor = Depends(get_current_proveedor),
    db: Session = Depends(get_db),
):
    """Estadísticas del proveedor para su dashboard."""
    return proveedor_service.obtener_dashboard_stats(proveedor, db)


@router.get("/{proveedor_id}", response_model=ProveedorOut)
def obtener_proveedor(proveedor_id: int, db: Session = Depends(get_db)):
    return proveedor_service.obtener_proveedor(proveedor_id, db)


@router.post("/", response_model=ProveedorOut, status_code=201)
def crear_proveedor(
    datos: ProveedorCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user)
):
    return proveedor_service.crear_proveedor(datos, db)


@router.patch("/{proveedor_id}", response_model=ProveedorOut)
def actualizar_proveedor(
    proveedor_id: int,
    datos: ProveedorUpdate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user)
):
    return proveedor_service.actualizar_proveedor(proveedor_id, datos, db)
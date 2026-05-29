from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database import get_db
from app.schemas.catalogo import PaqueteCreate, PaqueteUpdate, PaqueteOut
from app.services import paquete_service

router = APIRouter()


@router.get("/", response_model=List[PaqueteOut])
def listar_paquetes(
    proveedor_id: int = None,
    categoria_id: int = None,
    db: Session = Depends(get_db)
):
    """Lista paquetes activos con filtros opcionales."""
    return paquete_service.listar_paquetes(proveedor_id, categoria_id, db)


@router.get("/{paquete_id}", response_model=PaqueteOut)
def obtener_paquete(paquete_id: int, db: Session = Depends(get_db)):
    return paquete_service.obtener_paquete(paquete_id, db)


@router.post("/", response_model=PaqueteOut, status_code=201)
def crear_paquete(
    datos: PaqueteCreate,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user)
):
    """Crea un paquete con todos sus detalles en una sola operación."""
    return paquete_service.crear_paquete(datos, db)


@router.patch("/{paquete_id}", response_model=PaqueteOut)
def actualizar_paquete(
    paquete_id: int,
    datos: PaqueteUpdate,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user)
):
    return paquete_service.actualizar_paquete(paquete_id, datos, db)


@router.delete("/{paquete_id}", status_code=204)
def eliminar_paquete(
    paquete_id: int,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user)
):
    paquete_service.eliminar_paquete(paquete_id, db)

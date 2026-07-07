from typing import List

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_current_proveedor
from app.domain.personal.schemas import PersonalCreate, PersonalUpdate, PersonalOut
from app.domain.usuarios.models import Proveedor
from app.repositories.personal_repository import (
    PersonalRepository,
    PersonalRolRepository,
    get_personal_repo,
    get_personal_rol_repo
)
from app.services import personal_service

router = APIRouter()


@router.get("/proveedor/{proveedor_id}", response_model=List[PersonalOut])
def listar_personal(
    proveedor_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    repo: PersonalRepository = Depends(get_personal_repo),
):
    return personal_service.listar_personal_proveedor(proveedor_id, repo, skip=skip, limit=limit)


@router.get("/{personal_id}", response_model=PersonalOut)
def obtener_personal(personal_id: int, repo: PersonalRepository = Depends(get_personal_repo)):
    return personal_service.obtener_personal(personal_id, repo)


@router.post("/", response_model=PersonalOut, status_code=201)
def crear_personal(
    datos: PersonalCreate,
    proveedor: Proveedor = Depends(get_current_proveedor),
    repo: PersonalRepository = Depends(get_personal_repo),
    rol_repo: PersonalRolRepository = Depends(get_personal_rol_repo),
):
    """Crea una persona con sus roles asociados."""
    return personal_service.crear_personal(datos, proveedor, repo, rol_repo)


@router.patch("/{personal_id}", response_model=PersonalOut)
def actualizar_personal(
    personal_id: int,
    datos: PersonalUpdate,
    proveedor: Proveedor = Depends(get_current_proveedor),
    repo: PersonalRepository = Depends(get_personal_repo),
):
    """Actualiza datos base del personal (no roles por ahora)."""
    return personal_service.actualizar_personal(personal_id, datos, proveedor, repo)


@router.delete("/{personal_id}", status_code=204)
def eliminar_personal(
    personal_id: int,
    proveedor: Proveedor = Depends(get_current_proveedor),
    repo: PersonalRepository = Depends(get_personal_repo),
):
    """Soft delete del personal."""
    personal_service.eliminar_personal(personal_id, proveedor, repo)

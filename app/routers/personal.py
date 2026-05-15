from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database import get_db
from app.schemas.personal import PersonalCreate, PersonalUpdate, PersonalOut
from app.services import personal_service

router = APIRouter()


@router.get("/proveedor/{proveedor_id}", response_model=List[PersonalOut])
def listar_personal_proveedor(proveedor_id: int, db: Session = Depends(get_db)):
    """Lista todo el personal activo de un proveedor con sus roles."""
    return personal_service.listar_personal_proveedor(proveedor_id, db)


@router.get("/{personal_id}", response_model=PersonalOut)
def obtener_personal(personal_id: int, db: Session = Depends(get_db)):
    return personal_service.obtener_personal(personal_id, db)


@router.post("/", response_model=PersonalOut, status_code=201)
def crear_personal(
    datos: PersonalCreate,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user)
):
    """Crea una persona con sus roles en una sola operación."""
    return personal_service.crear_personal(datos, db)


@router.patch("/{personal_id}", response_model=PersonalOut)
def actualizar_personal(
    personal_id: int,
    datos: PersonalUpdate,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user)
):
    return personal_service.actualizar_personal(personal_id, datos, db)


@router.delete("/{personal_id}", status_code=204)
def eliminar_personal(
    personal_id: int,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user)
):
    """Soft delete: marca como INACTIVO sin borrar el registro."""
    personal_service.eliminar_personal(personal_id, db)
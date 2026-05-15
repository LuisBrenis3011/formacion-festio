from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database import get_db
from app.schemas.pago import ResenaCreate, ResenaOut
from app.services import resena_service

# ── Router Reseñas ────────────────────────────────────────────────────────────
router = APIRouter()


@router.get("/proveedor/{proveedor_id}", response_model=List[ResenaOut])
def reseñas_proveedor(proveedor_id: int, db: Session = Depends(get_db)):
    """Lista todas las reseñas de un proveedor."""
    return resena_service.listar_resenas_proveedor(proveedor_id, db)


@router.post("/", response_model=ResenaOut, status_code=201)
def crear_resena(
    datos: ResenaCreate,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user)
):
    """El cliente deja su reseña después de completar el evento."""
    return resena_service.crear_resena(datos, db)

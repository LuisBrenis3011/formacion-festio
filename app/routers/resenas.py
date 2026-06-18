from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.usuario import Usuario
from app.schemas.pago import ResenaCreate, ResenaOut
from app.schemas.resena import ResenaPublicaCreate, ResenaPublicaOut
from app.services import resena_service

# ── Router Reseñas ────────────────────────────────────────────────────────────
router = APIRouter()


@router.get("/proveedor/{proveedor_id}", response_model=List[ResenaPublicaOut])
def reseñas_proveedor(proveedor_id: int, db: Session = Depends(get_db)):
    """Lista todas las reseñas de un proveedor (público, con nombre de usuario)."""
    return resena_service.listar_resenas_publicas(proveedor_id, db)


@router.post("/", response_model=ResenaOut, status_code=201)
def crear_resena(
    datos: ResenaCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user)
):
    """El cliente deja su reseña después de completar el evento."""
    return resena_service.crear_resena(datos, db)


@router.post("/publica", response_model=ResenaPublicaOut, status_code=201)
def crear_resena_publica(
    datos: ResenaPublicaCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    """Crea una reseña pública. Requiere estar logueado."""
    resena = resena_service.crear_resena_publica(datos, usuario, db)
    # Convertir a ResenaPublicaOut
    nombre = f"{usuario.nombre} {usuario.apellido[0]}." if usuario.apellido else usuario.nombre
    return ResenaPublicaOut(
        id=resena.id,
        proveedor_id=resena.proveedor_id,
        calificacion=resena.calificacion,
        comentario=resena.comentario,
        fecha=resena.fecha,
        nombre_usuario=nombre,
    )

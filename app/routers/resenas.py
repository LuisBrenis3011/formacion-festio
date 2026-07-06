from typing import List

from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user
from app.domain.usuarios.models import Usuario
from app.domain.pagos.schemas import ResenaCreate, ResenaOut
from app.domain.resenas.schemas import ResenaPublicaCreate, ResenaPublicaOut
from app.repositories.resena_repository import ResenaRepository, get_resena_repo
from app.repositories.usuario_repository import ProveedorRepository, UsuarioRepository, get_proveedor_repo, get_usuario_repo
from app.services import resena_service

# ── Router Reseñas ────────────────────────────────────────────────────────────
router = APIRouter()


@router.get("/proveedor/{proveedor_id}", response_model=List[ResenaPublicaOut])
def reseñas_proveedor(
    proveedor_id: int,
    resena_repo: ResenaRepository = Depends(get_resena_repo),
    usuario_repo: UsuarioRepository = Depends(get_usuario_repo)
):
    """Lista todas las reseñas de un proveedor (público, con nombre de usuario)."""
    return resena_service.listar_resenas_publicas(proveedor_id, resena_repo, usuario_repo)


@router.post("/", response_model=ResenaOut, status_code=201)
def crear_resena(
    datos: ResenaCreate,
    resena_repo: ResenaRepository = Depends(get_resena_repo),
    proveedor_repo: ProveedorRepository = Depends(get_proveedor_repo),
    usuario: Usuario = Depends(get_current_user)
):
    """El cliente deja su reseña después de completar el evento."""
    return resena_service.crear_resena(datos, usuario, resena_repo, proveedor_repo)


@router.post("/publica", response_model=ResenaPublicaOut, status_code=201)
def crear_resena_publica(
    datos: ResenaPublicaCreate,
    resena_repo: ResenaRepository = Depends(get_resena_repo),
    proveedor_repo: ProveedorRepository = Depends(get_proveedor_repo),
    usuario: Usuario = Depends(get_current_user),
):
    """Crea una reseña pública. Requiere estar logueado."""
    resena = resena_service.crear_resena_publica(datos, usuario, resena_repo, proveedor_repo)
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

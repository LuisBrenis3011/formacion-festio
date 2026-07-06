from typing import List

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_current_user
from app.domain.usuarios.schemas import UsuarioOut
from app.repositories.usuario_repository import UsuarioRepository, get_usuario_repo
from app.services import usuario_service

router = APIRouter()


@router.get("/", response_model=List[UsuarioOut])
def listar_usuarios(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    repo: UsuarioRepository = Depends(get_usuario_repo),
    _: int = Depends(get_current_user),
):
    return usuario_service.listar_usuarios(repo, skip=skip, limit=limit)


@router.get("/{usuario_id}", response_model=UsuarioOut)
def obtener_usuario(
    usuario_id: int,
    repo: UsuarioRepository = Depends(get_usuario_repo),
    _: int = Depends(get_current_user),
):
    return usuario_service.obtener_usuario(usuario_id, repo)


@router.patch("/{usuario_id}/estado", response_model=UsuarioOut)
def actualizar_estado_usuario(
    usuario_id: int,
    estado: str,
    repo: UsuarioRepository = Depends(get_usuario_repo),
    _: int = Depends(get_current_user),
):
    return usuario_service.actualizar_estado_usuario(usuario_id, estado, repo)

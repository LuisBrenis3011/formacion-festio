from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database import get_db
from app.schemas.usuario import UsuarioOut
from app.services import usuario_service

router = APIRouter()


@router.get("/", response_model=List[UsuarioOut])
def listar_usuarios(db: Session = Depends(get_db), _: int = Depends(get_current_user)):
    return usuario_service.listar_usuarios(db)


@router.get("/{usuario_id}", response_model=UsuarioOut)
def obtener_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user),
):
    return usuario_service.obtener_usuario(usuario_id, db)


@router.patch("/{usuario_id}/estado", response_model=UsuarioOut)
def actualizar_estado_usuario(
    usuario_id: int,
    estado: str,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user),
):
    return usuario_service.actualizar_estado_usuario(usuario_id, estado, db)

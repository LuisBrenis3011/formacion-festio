from typing import List

from fastapi import HTTPException

from app.domain.common.enums import EstadoBasico
from app.domain.usuarios.models import Usuario
from app.repositories.usuario_repository import UsuarioRepository


def listar_usuarios(repo: UsuarioRepository, skip: int = 0, limit: int = 100) -> List[Usuario]:
    """Retorna todos los usuarios registrados."""
    return repo.get_all(skip=skip, limit=limit)


def obtener_usuario(usuario_id: int, repo: UsuarioRepository) -> Usuario:
    """Busca un usuario por ID. Lanza 404 si no existe."""
    usuario = repo.get(usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario


def actualizar_estado_usuario(usuario_id: int, estado: str, repo: UsuarioRepository) -> Usuario:
    """Actualiza el estado de un usuario. Valida que el estado sea válido."""
    usuario = repo.get(usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    try:
        estado_enum = EstadoBasico(estado)
    except ValueError:
        raise HTTPException(status_code=400, detail="Estado inválido. Use ACTIVO o INACTIVO")

    usuario.estado = estado_enum
    repo.db.commit()
    repo.db.refresh(usuario)
    return usuario

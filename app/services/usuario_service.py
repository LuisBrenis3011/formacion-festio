from typing import List

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.enums import EstadoBasico
from app.models.usuario import Usuario


def listar_usuarios(db: Session) -> List[Usuario]:
    """Retorna todos los usuarios registrados."""
    return db.query(Usuario).all()


def obtener_usuario(usuario_id: int, db: Session) -> Usuario:
    """Busca un usuario por ID. Lanza 404 si no existe."""
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario


def actualizar_estado_usuario(usuario_id: int, estado: str, db: Session) -> Usuario:
    """Actualiza el estado de un usuario. Valida que el estado sea válido."""
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    try:
        estado_enum = EstadoBasico(estado)
    except ValueError:
        raise HTTPException(status_code=400, detail="Estado inválido. Use ACTIVO o INACTIVO")

    usuario.estado = estado_enum
    db.commit()
    db.refresh(usuario)
    return usuario

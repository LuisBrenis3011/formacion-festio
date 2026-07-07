from typing import List

from fastapi import HTTPException

from app.domain.common.enums import EstadoBasico
from app.domain.personal.models import Personal, PersonalRol
from app.domain.personal.schemas import PersonalCreate, PersonalUpdate
from app.repositories.personal_repository import PersonalRepository, PersonalRolRepository


def listar_personal_proveedor(proveedor_id: int, repo: PersonalRepository) -> List[Personal]:
    """Lista todo el personal activo de un proveedor con sus roles."""
    return repo.db.query(Personal).filter(
        Personal.proveedor_id == proveedor_id,
        Personal.estado == EstadoBasico.ACTIVO
    ).all()


def obtener_personal(personal_id: int, repo: PersonalRepository) -> Personal:
    """Busca personal por ID. Lanza 404 si no existe."""
    persona = repo.get(personal_id)
    if not persona:
        raise HTTPException(status_code=404, detail="Personal no encontrado")
    return persona


def crear_personal(datos: PersonalCreate, repo: PersonalRepository, rol_repo: PersonalRolRepository) -> Personal:
    """Crea una persona con sus roles en una sola operación."""
    persona = Personal(
        proveedor_id=datos.proveedor_id,
        nombre=datos.nombre,
        telefono=datos.telefono,
    )
    repo.db.add(persona)
    repo.db.flush()

    for rol_data in datos.roles:
        rol_repo.db.add(PersonalRol(
            personal_id=persona.id,
            rol=rol_data.rol,
            precio_por_rol=rol_data.precio_por_rol,
            rol_principal=rol_data.rol_principal,
        ))

    repo.db.commit()
    repo.db.refresh(persona)
    return persona


def actualizar_personal(
    personal_id: int, datos: PersonalUpdate, repo: PersonalRepository
) -> Personal:
    """Actualiza los campos enviados del personal. Lanza 404 si no existe."""
    persona = repo.update(personal_id, datos)
    if not persona:
        raise HTTPException(status_code=404, detail="Personal no encontrado")
    return persona


def eliminar_personal(personal_id: int, repo: PersonalRepository) -> None:
    """Soft delete: marca como INACTIVO sin borrar el registro."""
    persona = repo.get(personal_id)
    if not persona:
        raise HTTPException(status_code=404, detail="Personal no encontrado")

    persona.estado = EstadoBasico.INACTIVO
    repo.db.commit()

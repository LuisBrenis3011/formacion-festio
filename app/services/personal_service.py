from typing import List

from fastapi import HTTPException

from app.domain.common.enums import EstadoBasico
from app.domain.personal.models import Personal, PersonalRol
from app.domain.personal.schemas import PersonalCreate, PersonalUpdate
from app.domain.usuarios.models import Proveedor
from app.repositories.personal_repository import PersonalRepository, PersonalRolRepository


def listar_personal_proveedor(proveedor_id: int, repo: PersonalRepository, skip: int = 0, limit: int = 100) -> List[Personal]:
    return repo.db.query(Personal).filter(
        Personal.proveedor_id == proveedor_id,
        Personal.estado == EstadoBasico.ACTIVO
    ).offset(skip).limit(limit).all()


def obtener_personal(personal_id: int, repo: PersonalRepository) -> Personal:
    """Busca personal por ID. Lanza 404 si no existe."""
    persona = repo.get(personal_id)
    if not persona:
        raise HTTPException(status_code=404, detail="Personal no encontrado")
    return persona


def crear_personal(
    datos: PersonalCreate,
    proveedor: Proveedor,
    repo: PersonalRepository,
    rol_repo: PersonalRolRepository,
) -> Personal:
    """Crea una persona con sus roles en una sola operación."""
    # El proveedor del body debe coincidir con el proveedor resuelto desde el token.
    if datos.proveedor_id != proveedor.id:
        raise HTTPException(
            status_code=403,
            detail="No puede crear personal para otro proveedor",
        )

    persona = Personal(
        proveedor_id=proveedor.id,
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
    personal_id: int,
    datos: PersonalUpdate,
    proveedor: Proveedor,
    repo: PersonalRepository,
) -> Personal:
    """Actualiza los campos enviados del personal. Lanza 404 si no existe."""
    persona = _obtener_personal_proveedor(personal_id, proveedor, repo)

    # Primero cargamos el registro propio del proveedor y luego aplicamos solo los campos enviados.
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(persona, campo, valor)

    repo.db.commit()
    repo.db.refresh(persona)
    return persona


def eliminar_personal(personal_id: int, proveedor: Proveedor, repo: PersonalRepository) -> None:
    """Soft delete: marca como INACTIVO sin borrar el registro."""
    persona = _obtener_personal_proveedor(personal_id, proveedor, repo)

    persona.estado = EstadoBasico.INACTIVO
    repo.db.commit()


def _obtener_personal_proveedor(
    personal_id: int,
    proveedor: Proveedor,
    repo: PersonalRepository,
) -> Personal:
    # Centraliza el filtro de ownership para que update/delete no operen sobre personal ajeno por ID.
    persona = repo.db.query(Personal).filter(
        Personal.id == personal_id,
        Personal.proveedor_id == proveedor.id,
    ).first()
    if not persona:
        raise HTTPException(status_code=404, detail="Personal no encontrado")
    return persona

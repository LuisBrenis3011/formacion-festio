from typing import List

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.domain.common.enums import EstadoBasico
from app.domain.personal.models import Personal, PersonalRol
from app.domain.personal.schemas import PersonalCreate, PersonalUpdate


def listar_personal_proveedor(proveedor_id: int, db: Session) -> List[Personal]:
    """Lista todo el personal activo de un proveedor con sus roles."""
    return db.query(Personal).filter(
        Personal.proveedor_id == proveedor_id,
        Personal.estado == EstadoBasico.ACTIVO
    ).all()


def obtener_personal(personal_id: int, db: Session) -> Personal:
    """Busca personal por ID. Lanza 404 si no existe."""
    persona = db.query(Personal).filter(Personal.id == personal_id).first()
    if not persona:
        raise HTTPException(status_code=404, detail="Personal no encontrado")
    return persona


def crear_personal(datos: PersonalCreate, db: Session) -> Personal:
    """Crea una persona con sus roles en una sola operación."""
    persona = Personal(
        proveedor_id=datos.proveedor_id,
        nombre=datos.nombre,
        telefono=datos.telefono,
    )
    db.add(persona)
    db.flush()

    for rol_data in datos.roles:
        db.add(PersonalRol(
            personal_id=persona.id,
            rol=rol_data.rol,
            precio_por_rol=rol_data.precio_por_rol,
            rol_principal=rol_data.rol_principal,
        ))

    db.commit()
    db.refresh(persona)
    return persona


def actualizar_personal(
    personal_id: int, datos: PersonalUpdate, db: Session
) -> Personal:
    """Actualiza los campos enviados del personal. Lanza 404 si no existe."""
    persona = db.query(Personal).filter(Personal.id == personal_id).first()
    if not persona:
        raise HTTPException(status_code=404, detail="Personal no encontrado")

    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(persona, campo, valor)

    db.commit()
    db.refresh(persona)
    return persona


def eliminar_personal(personal_id: int, db: Session) -> None:
    """Soft delete: marca como INACTIVO sin borrar el registro."""
    persona = db.query(Personal).filter(Personal.id == personal_id).first()
    if not persona:
        raise HTTPException(status_code=404, detail="Personal no encontrado")

    persona.estado = EstadoBasico.INACTIVO
    db.commit()

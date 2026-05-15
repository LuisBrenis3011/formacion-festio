from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.enums import EstadoVerificacion
from app.models.usuario import Proveedor
from app.schemas.usuario import ProveedorCreate, ProveedorUpdate


def listar_proveedores(distrito: Optional[str], db: Session) -> List[Proveedor]:
    """Lista proveedores verificados. Filtra por distrito si se indica."""
    query = db.query(Proveedor).filter(
        Proveedor.estado_verificacion == EstadoVerificacion.VERIFICADO
    )
    if distrito:
        query = query.filter(Proveedor.distrito.ilike(f"%{distrito}%"))
    return query.all()


def obtener_proveedor(proveedor_id: int, db: Session) -> Proveedor:
    """Busca un proveedor por ID. Lanza 404 si no existe."""
    proveedor = db.query(Proveedor).filter(Proveedor.id == proveedor_id).first()
    if not proveedor:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    return proveedor


def crear_proveedor(datos: ProveedorCreate, db: Session) -> Proveedor:
    """Crea un nuevo proveedor a partir de los datos validados."""
    proveedor = Proveedor(**datos.model_dump())
    db.add(proveedor)
    db.commit()
    db.refresh(proveedor)
    return proveedor


def actualizar_proveedor(
    proveedor_id: int, datos: ProveedorUpdate, db: Session
) -> Proveedor:
    """Actualiza los campos enviados del proveedor. Lanza 404 si no existe."""
    proveedor = db.query(Proveedor).filter(Proveedor.id == proveedor_id).first()
    if not proveedor:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")

    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(proveedor, campo, valor)

    db.commit()
    db.refresh(proveedor)
    return proveedor

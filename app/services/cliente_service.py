from typing import List

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.usuario import Cliente
from app.schemas.usuario import ClienteCreate


def listar_clientes(db: Session) -> List[Cliente]:
    """Retorna todos los clientes registrados."""
    return db.query(Cliente).all()


def obtener_cliente(cliente_id: int, db: Session) -> Cliente:
    """Busca un cliente por ID. Lanza 404 si no existe."""
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return cliente


def crear_cliente(datos: ClienteCreate, db: Session) -> Cliente:
    """Crea un nuevo cliente a partir de los datos validados."""
    cliente = Cliente(**datos.model_dump())
    db.add(cliente)
    db.commit()
    db.refresh(cliente)
    return cliente

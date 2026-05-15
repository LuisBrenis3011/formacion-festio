from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database import get_db
from app.schemas.usuario import ClienteCreate, ClienteOut
from app.services import cliente_service

router = APIRouter()


@router.get("/", response_model=List[ClienteOut])
def listar_clientes(db: Session = Depends(get_db), _: int = Depends(get_current_user)):
    return cliente_service.listar_clientes(db)


@router.get("/{cliente_id}", response_model=ClienteOut)
def obtener_cliente(
    cliente_id: int,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user),
):
    return cliente_service.obtener_cliente(cliente_id, db)


@router.post("/", response_model=ClienteOut, status_code=201)
def crear_cliente(
    datos: ClienteCreate,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user),
):
    return cliente_service.crear_cliente(datos, db)

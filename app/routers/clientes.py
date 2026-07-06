from typing import List
from fastapi import APIRouter, Depends, Query
from app.domain.usuarios.schemas import ClienteCreate, ClienteOut
from app.repositories.usuario_repository import ClienteRepository, get_cliente_repo
from app.services import cliente_service

router = APIRouter()

@router.get("/", response_model=List[ClienteOut])
def listar_clientes(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    repo: ClienteRepository = Depends(get_cliente_repo),
):
    return cliente_service.listar_clientes(repo, skip=skip, limit=limit)

@router.get("/{cliente_id}", response_model=ClienteOut)
def obtener_cliente(cliente_id: int, repo: ClienteRepository = Depends(get_cliente_repo)):
    return cliente_service.obtener_cliente(cliente_id, repo)

@router.post("/", response_model=ClienteOut, status_code=201)
def crear_cliente(datos: ClienteCreate, repo: ClienteRepository = Depends(get_cliente_repo)):
    return cliente_service.crear_cliente(datos, repo)

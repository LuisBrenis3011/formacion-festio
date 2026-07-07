from typing import List
from fastapi import HTTPException
from app.domain.usuarios.models import Cliente
from app.domain.usuarios.schemas import ClienteCreate
from app.repositories.usuario_repository import ClienteRepository

def listar_clientes(repo: ClienteRepository) -> List[Cliente]:
    return repo.get_all()

def obtener_cliente(cliente_id: int, repo: ClienteRepository) -> Cliente:
    cliente = repo.get(cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return cliente

def crear_cliente(datos: ClienteCreate, repo: ClienteRepository) -> Cliente:
    return repo.create(datos)

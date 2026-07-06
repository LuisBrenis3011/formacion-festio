from typing import List

from fastapi import APIRouter, Depends

from app.core.dependencies import require_role
from app.domain.common.enums import RolUsuario
from app.domain.usuarios.models import Usuario
from app.domain.usuarios.schemas import ClienteCreate, ClienteOut
from app.repositories.usuario_repository import ClienteRepository, get_cliente_repo
from app.services import cliente_service

router = APIRouter()


@router.get("/", response_model=List[ClienteOut])
def listar_clientes(
    repo: ClienteRepository = Depends(get_cliente_repo),
    _: Usuario = Depends(require_role(RolUsuario.ADMIN)),
):
    # El alta publica de clientes vive en /api/auth/registro; este CRUD queda para uso administrativo.
    return cliente_service.listar_clientes(repo)


@router.get("/{cliente_id}", response_model=ClienteOut)
def obtener_cliente(
    cliente_id: int,
    repo: ClienteRepository = Depends(get_cliente_repo),
    _: Usuario = Depends(require_role(RolUsuario.ADMIN)),
):
    return cliente_service.obtener_cliente(cliente_id, repo)


@router.post("/", response_model=ClienteOut, status_code=201)
def crear_cliente(
    datos: ClienteCreate,
    repo: ClienteRepository = Depends(get_cliente_repo),
    _: Usuario = Depends(require_role(RolUsuario.ADMIN)),
):
    return cliente_service.crear_cliente(datos, repo)

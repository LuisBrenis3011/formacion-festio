from fastapi import APIRouter, Depends
from app.core.dependencies import get_current_user
from app.domain.usuarios.models import Usuario
from app.domain.usuarios.schemas import (
    UsuarioCreate, UsuarioOut, LoginRequest, TokenResponse,
    RegistroProveedorRequest, MeResponse,
)
from app.repositories.usuario_repository import (
    UsuarioRepository, ClienteRepository, ProveedorRepository,
    get_usuario_repo, get_cliente_repo, get_proveedor_repo
)
from app.services import auth_service

router = APIRouter()


@router.post("/registro", response_model=UsuarioOut, status_code=201)
def registrar(
    datos: UsuarioCreate,
    usuario_repo: UsuarioRepository = Depends(get_usuario_repo),
    cliente_repo: ClienteRepository = Depends(get_cliente_repo)
):
    """Registra un nuevo cliente desde el flujo publico."""
    return auth_service.registrar_usuario(datos, usuario_repo, cliente_repo)


@router.post("/registro-proveedor", response_model=TokenResponse, status_code=201)
def registrar_proveedor(
    datos: RegistroProveedorRequest,
    usuario_repo: UsuarioRepository = Depends(get_usuario_repo),
    proveedor_repo: ProveedorRepository = Depends(get_proveedor_repo)
):
    """Registra un proveedor con datos de empresa y devuelve token directo."""
    return auth_service.registrar_proveedor(datos, usuario_repo, proveedor_repo)


@router.post("/login", response_model=TokenResponse)
def login(
    datos: LoginRequest,
    usuario_repo: UsuarioRepository = Depends(get_usuario_repo)
):
    """Inicia sesión y retorna el token JWT."""
    return auth_service.login(datos, usuario_repo)


@router.get("/me", response_model=MeResponse)
def me(usuario: Usuario = Depends(get_current_user)):
    """Retorna los datos del usuario autenticado."""
    return auth_service.get_me(usuario)

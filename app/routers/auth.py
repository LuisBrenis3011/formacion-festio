from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.usuario import Usuario
from app.schemas.usuario import (
    UsuarioCreate, UsuarioOut, LoginRequest, TokenResponse,
    RegistroProveedorRequest, MeResponse,
)
from app.services import auth_service

router = APIRouter()


@router.post("/registro", response_model=UsuarioOut, status_code=201)
def registrar(datos: UsuarioCreate, db: Session = Depends(get_db)):
    """Registra un nuevo usuario (cliente o proveedor)."""
    return auth_service.registrar_usuario(datos, db)


@router.post("/registro-proveedor", response_model=TokenResponse, status_code=201)
def registrar_proveedor(datos: RegistroProveedorRequest, db: Session = Depends(get_db)):
    """Registra un proveedor con datos de empresa y devuelve token directo."""
    return auth_service.registrar_proveedor(datos, db)


@router.post("/login", response_model=TokenResponse)
def login(datos: LoginRequest, db: Session = Depends(get_db)):
    """Inicia sesión y retorna el token JWT."""
    return auth_service.login(datos, db)


@router.get("/me", response_model=MeResponse)
def me(usuario: Usuario = Depends(get_current_user)):
    """Retorna los datos del usuario autenticado."""
    return auth_service.get_me(usuario)
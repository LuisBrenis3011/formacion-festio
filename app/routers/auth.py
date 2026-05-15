from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.usuario import UsuarioCreate, UsuarioOut, LoginRequest, TokenResponse
from app.services import auth_service

router = APIRouter()


@router.post("/registro", response_model=UsuarioOut, status_code=201)
def registrar(datos: UsuarioCreate, db: Session = Depends(get_db)):
    """Registra un nuevo usuario (cliente o proveedor)."""
    return auth_service.registrar_usuario(datos, db)


@router.post("/login", response_model=TokenResponse)
def login(datos: LoginRequest, db: Session = Depends(get_db)):
    """Inicia sesión y retorna el token JWT."""
    return auth_service.login(datos, db)
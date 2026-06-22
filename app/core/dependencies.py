from typing import Callable, List, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.security import decode_token
from app.models.enums import RolUsuario
from app.models.usuario import Usuario, Proveedor

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
optional_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def _user_from_token(token: str, db: Session) -> Usuario:
    """Decodifica el JWT y retorna el objeto Usuario completo."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar las credenciales",
    )
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except Exception:
        raise credentials_exception

    usuario = db.query(Usuario).filter(Usuario.id == int(user_id)).first()
    if usuario is None:
        raise credentials_exception
    return usuario


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Usuario:
    return _user_from_token(token, db)


def get_optional_current_user(
    token: Optional[str] = Depends(optional_oauth2_scheme),
    db: Session = Depends(get_db),
) -> Optional[Usuario]:
    """Retorna el usuario si llega Authorization; mantiene público el endpoint si no llega."""
    if not token:
        return None
    return _user_from_token(token, db)


def require_role(*roles: RolUsuario) -> Callable:
    """Factory que genera una dependencia que valida el rol del usuario.

    Uso:
        @router.get("/...", dependencies=[Depends(require_role(RolUsuario.PROVEEDOR))])
        def mi_endpoint(usuario: Usuario = Depends(get_current_user)):
            ...
    """
    def _checker(usuario: Usuario = Depends(get_current_user)) -> Usuario:
        # usuario.rol es un Enum; comparamos directamente
        if usuario.rol not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Se requiere rol: {', '.join(r.value for r in roles)}",
            )
        return usuario
    return _checker


def get_current_proveedor(
    usuario: Usuario = Depends(require_role(RolUsuario.PROVEEDOR)),
    db: Session = Depends(get_db),
) -> Proveedor:
    """Shortcut: retorna el Proveedor asociado al usuario logueado.
    Lanza 404 si el usuario PROVEEDOR no tiene perfil de proveedor aún."""
    proveedor = db.query(Proveedor).filter(
        Proveedor.usuario_id == usuario.id
    ).first()
    if not proveedor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil de proveedor no encontrado. Complete su registro.",
        )
    return proveedor

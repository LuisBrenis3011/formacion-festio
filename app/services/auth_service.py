from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.enums import EstadoBasico, RolUsuario
from app.models.usuario import Usuario, Cliente, Proveedor
from app.schemas.usuario import UsuarioCreate, LoginRequest, TokenResponse
from app.core.security import hash_password, verify_password, create_access_token


def registrar_usuario(datos: UsuarioCreate, db: Session) -> Usuario:
    existe = db.query(Usuario).filter(Usuario.email == datos.email).first()
    if existe:
        raise HTTPException(status_code=400, detail="El email ya está registrado")

    usuario = Usuario(
        nombre          = datos.nombre,
        apellido        = datos.apellido,
        email           = datos.email,
        telefono        = datos.telefono,
        contrasena_hash = hash_password(datos.password),
        rol             = datos.rol,
    )
    db.add(usuario)
    db.flush()  # Obtener el ID antes del commit

    # Crear perfil según el rol
    if datos.rol == RolUsuario.CLIENTE:
        db.add(Cliente(usuario_id=usuario.id))
    elif datos.rol == RolUsuario.PROVEEDOR:
        db.add(Proveedor(usuario_id=usuario.id, nombre_empresa=datos.nombre, ruc="", distrito=""))

    db.commit()
    db.refresh(usuario)
    return usuario


def login(datos: LoginRequest, db: Session) -> TokenResponse:
    usuario = db.query(Usuario).filter(Usuario.email == datos.email).first()

    if not usuario or not verify_password(datos.password, usuario.contrasena_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas"
        )

    if usuario.estado == EstadoBasico.INACTIVO:
        raise HTTPException(status_code=403, detail="Cuenta inactiva")

    token = create_access_token({"sub": str(usuario.id), "rol": usuario.rol})
    return TokenResponse(access_token=token, token_type="bearer", rol=usuario.rol)

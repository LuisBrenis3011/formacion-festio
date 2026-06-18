from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.enums import EstadoBasico, RolUsuario
from app.models.usuario import Usuario, Cliente, Proveedor
from app.schemas.usuario import (
    UsuarioCreate, LoginRequest, TokenResponse,
    RegistroProveedorRequest, MeResponse,
)
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


def registrar_proveedor(datos: RegistroProveedorRequest, db: Session) -> TokenResponse:
    """Registro específico para proveedores con datos de empresa."""
    existe = db.query(Usuario).filter(Usuario.email == datos.email).first()
    if existe:
        raise HTTPException(status_code=400, detail="El email ya está registrado")

    usuario = Usuario(
        nombre          = datos.nombre,
        apellido        = datos.apellido,
        email           = datos.email,
        telefono        = datos.telefono,
        contrasena_hash = hash_password(datos.password),
        rol             = RolUsuario.PROVEEDOR,
    )
    db.add(usuario)
    db.flush()

    proveedor = Proveedor(
        usuario_id             = usuario.id,
        nombre_empresa         = datos.nombre_empresa,
        ruc                    = datos.ruc,
        descripcion            = datos.descripcion,
        distrito               = datos.distrito,
        capacidad_humana_total = datos.capacidad_humana_total or 0,
    )
    db.add(proveedor)
    db.commit()
    db.refresh(usuario)
    db.refresh(proveedor)

    token = create_access_token({"sub": str(usuario.id), "rol": usuario.rol.value})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        rol=usuario.rol,
        usuario_id=usuario.id,
        nombre=usuario.nombre,
        proveedor_id=proveedor.id,
    )


def login(datos: LoginRequest, db: Session) -> TokenResponse:
    usuario = db.query(Usuario).filter(Usuario.email == datos.email).first()

    if not usuario or not verify_password(datos.password, usuario.contrasena_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas"
        )

    if usuario.estado == EstadoBasico.INACTIVO:
        raise HTTPException(status_code=403, detail="Cuenta inactiva")

    # Obtener proveedor_id si es PROVEEDOR
    proveedor_id = None
    if usuario.rol == RolUsuario.PROVEEDOR and usuario.proveedor:
        proveedor_id = usuario.proveedor.id

    token = create_access_token({"sub": str(usuario.id), "rol": usuario.rol.value})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        rol=usuario.rol,
        usuario_id=usuario.id,
        nombre=usuario.nombre,
        proveedor_id=proveedor_id,
    )


def get_me(usuario: Usuario) -> MeResponse:
    """Retorna datos del usuario logueado para el frontend."""
    proveedor_id = None
    nombre_empresa = None
    if usuario.rol == RolUsuario.PROVEEDOR and usuario.proveedor:
        proveedor_id = usuario.proveedor.id
        nombre_empresa = usuario.proveedor.nombre_empresa

    return MeResponse(
        id=usuario.id,
        nombre=usuario.nombre,
        apellido=usuario.apellido,
        email=usuario.email,
        rol=usuario.rol,
        estado=usuario.estado,
        proveedor_id=proveedor_id,
        nombre_empresa=nombre_empresa,
    )

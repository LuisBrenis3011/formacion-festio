"""
tests/conftest.py

TASK-TEST-06 — Configurar conftest.py con BD de pruebas.

Imports y fixtures verificados contra:
- app/database.py (Base, get_db)
- app/core/security.py (hash_password, create_access_token)
- app/core/dependencies.py (get_current_user solo usa el claim "sub")
- app/domain/usuarios/models.py (Usuario, Cliente, Proveedor)
- app/domain/common/enums.py (RolUsuario, EstadoBasico, EstadoVerificacion)

⚠️ Único punto aún no confirmado: si `app/redis_client.py` expone el
objeto `redis_client` a nivel de módulo (para que el monkeypatch de
`mock_redis` funcione). Si algún servicio hace
`from app.redis_client import redis_client` de forma directa en vez de
`import app.redis_client as redis_client_module`, ese servicio no
quedará mockeado con este fixture — habría que ajustarlo puntualmente.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import MagicMock

from app.main import app
from app.database import Base, get_db

# AJUSTAR: confirma que redis_client.py expone un objeto llamado `redis_client`
# a nivel de módulo (from app import redis_client as redis_client_module,
# y luego redis_client_module.redis_client)
from app import redis_client as redis_client_module

from app.domain.usuarios.models import Usuario, Cliente, Proveedor
from app.domain.common.enums import RolUsuario, EstadoBasico, EstadoVerificacion

from app.core.security import create_access_token, hash_password


# ---------------------------------------------------------------------------
# 1. Base de datos SQLite en memoria
# ---------------------------------------------------------------------------
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,  # misma conexión en memoria para todo el test
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Crea todas las tablas antes de cada test y las destruye después."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


# ---------------------------------------------------------------------------
# 2. TestClient con override de get_db
# ---------------------------------------------------------------------------
@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# 3. Mock de Redis (autouse=True para que aplique a todos los tests)
# ---------------------------------------------------------------------------
@pytest.fixture(scope="function", autouse=True)
def mock_redis(monkeypatch):
    fake_redis = MagicMock()
    fake_redis.get.return_value = None
    fake_redis.set.return_value = True
    fake_redis.setex.return_value = True
    fake_redis.delete.return_value = 1  # redis-py real devuelve un int, no bool
    fake_redis.exists.return_value = False

    # Si en tu código haces `from app.redis_client import redis_client`
    # (import directo del objeto, no del módulo) este monkeypatch no basta:
    # habría que mockear en cada archivo que hace ese import directo, o
    # cambiar esos imports a `import app.redis_client as redis_client_module`.
    monkeypatch.setattr(redis_client_module, "redis_client", fake_redis)
    return fake_redis


# ---------------------------------------------------------------------------
# 4. Fixtures de usuario autenticado (cliente y proveedor)
# ---------------------------------------------------------------------------
@pytest.fixture
def usuario_cliente(db_session):
    usuario = Usuario(
        nombre="Cliente",
        apellido="Test",
        email="cliente@test.com",
        telefono="987654321",
        contrasena_hash=hash_password("Password123!"),
        rol=RolUsuario.CLIENTE,
        estado=EstadoBasico.ACTIVO,
    )
    db_session.add(usuario)
    db_session.commit()
    db_session.refresh(usuario)

    cliente = Cliente(usuario_id=usuario.id, direccion="Av. Test 123")
    db_session.add(cliente)
    db_session.commit()

    return usuario


@pytest.fixture
def usuario_proveedor(db_session):
    usuario = Usuario(
        nombre="Proveedor",
        apellido="Test",
        email="proveedor@test.com",
        telefono="987654322",
        contrasena_hash=hash_password("Password123!"),
        rol=RolUsuario.PROVEEDOR,
        estado=EstadoBasico.ACTIVO,
    )
    db_session.add(usuario)
    db_session.commit()
    db_session.refresh(usuario)

    proveedor = Proveedor(
        usuario_id=usuario.id,
        nombre_empresa="Empresa Test SAC",
        ruc="20123456789",
        distrito="Miraflores",
        estado_verificacion=EstadoVerificacion.VERIFICADO,
    )
    db_session.add(proveedor)
    db_session.commit()

    return usuario


@pytest.fixture
def usuario_proveedor_pendiente(db_session):
    """Proveedor todavía no verificado, para tests de flujos que dependan de eso."""
    usuario = Usuario(
        nombre="ProveedorPendiente",
        apellido="Test",
        email="proveedor.pendiente@test.com",
        telefono="987654323",
        contrasena_hash=hash_password("Password123!"),
        rol=RolUsuario.PROVEEDOR,
        estado=EstadoBasico.ACTIVO,
    )
    db_session.add(usuario)
    db_session.commit()
    db_session.refresh(usuario)

    proveedor = Proveedor(
        usuario_id=usuario.id,
        nombre_empresa="Empresa Pendiente SAC",
        ruc="20987654321",
        distrito="Surco",
        # sin estado_verificacion -> queda en el default PENDIENTE
    )
    db_session.add(proveedor)
    db_session.commit()

    return usuario


@pytest.fixture
def usuario_inactivo(db_session):
    """Usuario con estado=INACTIVO, para tests de login bloqueado."""
    usuario = Usuario(
        nombre="Inactivo",
        apellido="Test",
        email="inactivo@test.com",
        telefono="987654324",
        contrasena_hash=hash_password("Password123!"),
        rol=RolUsuario.CLIENTE,
        estado=EstadoBasico.INACTIVO,
    )
    db_session.add(usuario)
    db_session.commit()
    db_session.refresh(usuario)
    return usuario


def _token_para(usuario):
    # Confirmado en dependencies.py: get_current_user solo lee el claim "sub"
    # (id de usuario) y resuelve el rol consultando la BD, no desde el token.
    return create_access_token({"sub": str(usuario.id)})


@pytest.fixture
def token_cliente(usuario_cliente):
    return _token_para(usuario_cliente)


@pytest.fixture
def token_proveedor(usuario_proveedor):
    return _token_para(usuario_proveedor)


@pytest.fixture
def auth_headers_cliente(token_cliente):
    return {"Authorization": f"Bearer {token_cliente}"}


@pytest.fixture
def auth_headers_proveedor(token_proveedor):
    return {"Authorization": f"Bearer {token_proveedor}"}
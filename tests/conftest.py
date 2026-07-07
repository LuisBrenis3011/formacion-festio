"""
tests/conftest.py

TASK-TEST-06 — Configurar conftest.py con BD de pruebas.

Imports y fixtures verificados contra:
- app/database.py (Base, get_db)
- app/core/security.py (hash_password, create_access_token)
- app/core/dependencies.py (get_current_user solo usa el claim "sub")
- app/domain/usuarios/models.py (Usuario, Cliente, Proveedor)
- app/domain/common/enums.py (RolUsuario, EstadoBasico, EstadoVerificacion)

- app/services/bloqueo_service.py (crear_bloqueo, obtener_bloqueo, liberar_bloqueo, listar_bloqueos)

"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import fnmatch

from app.main import app
from app.database import Base, get_db

# AJUSTAR: confirma que redis_client.py expone un objeto llamado `redis_client`
# a nivel de módulo (from app import redis_client as redis_client_module,
# y luego redis_client_module.redis_client)
from app import redis_client as redis_client_module

# bloqueo_service.py hace `from app.redis_client import redis_client` (import
# directo del objeto), así que además de parchear el módulo hay que parchear
# también la referencia ya capturada dentro de ese servicio.
from app.services import bloqueo_service

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
    """
    Fake de Redis CON ESTADO (no un MagicMock plano), porque los tests de
    checkout necesitan que crear_bloqueo() -> obtener_bloqueo() -> liberar_bloqueo()
    funcionen como un round-trip real dentro del mismo test.

    Cubre los métodos más comunes de redis-py. Cualquier método no definido
    explícitamente cae en __getattr__ y devuelve un MagicMock inofensivo, para
    no romper si algún servicio llama algo que no anticipamos aquí.
    """
    import fnmatch
    from unittest.mock import MagicMock as _MagicMock

    class FakeRedis:
        def __init__(self):
            self._store: dict = {}

        def get(self, key):
            return self._store.get(key)

        def set(self, key, value, *args, **kwargs):
            self._store[key] = value
            return True

        def setex(self, name, time, value):
            self._store[name] = value
            return True

        def delete(self, *keys):
            borrados = 0
            for k in keys:
                if k in self._store:
                    del self._store[k]
                    borrados += 1
            return borrados

        def exists(self, key):
            return 1 if key in self._store else 0

        def keys(self, pattern="*"):
            return [k for k in self._store if fnmatch.fnmatch(k, pattern)]

        def scan_iter(self, match="*", **kwargs):
            return iter(self.keys(match))

        def __getattr__(self, name):
            return _MagicMock()

    fake_redis = FakeRedis()

    # Parcheamos AMBAS referencias: el módulo (por si algo hace
    # `import app.redis_client as x` y usa `x.redis_client`) y la copia
    # directa que bloqueo_service.py capturó con `from ... import redis_client`.
    monkeypatch.setattr(redis_client_module, "redis_client", fake_redis)
    monkeypatch.setattr(bloqueo_service, "redis_client", fake_redis)
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
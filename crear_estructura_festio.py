import os

BASE = r"D:\desarrollo-uni\formación-festio"

estructura = {
    # Raíz del proyecto
    "": [
        ".env",
        ".env.example",
        ".gitignore",
        "requirements.txt",
        "alembic.ini",
        "README.md",
    ],

    # App principal
    "app": ["__init__.py", "main.py", "config.py", "database.py", "redis_client.py"],

    # Modelos SQLAlchemy (tablas de la BD)
    "app/models": [
        "__init__.py",
        "usuario.py",       # Usuario, Cliente, Proveedor
        "personal.py",      # Personal, Personal_Rol
        "catalogo.py",      # Categoria, Tematica, Servicio_Producto, Paquete, Detalle_Paquete
        "disponibilidad.py",# Ocupacion_Global_Proveedor, Ocupacion_Servicio_Producto
        "reserva.py",       # Evento, Reserva, Detalle_Reserva, Detalle_Reserva_Personal
        "pago.py",          # Pago_Transaccion, Comprobante
        "resena.py",        # Reseña
        "notificacion.py",  # Notificacion
    ],

    # Schemas Pydantic (validación de datos entrada/salida)
    "app/schemas": [
        "__init__.py",
        "usuario.py",
        "personal.py",
        "catalogo.py",
        "disponibilidad.py",
        "reserva.py",
        "pago.py",
        "resena.py",
        "notificacion.py",
    ],

    # Routers FastAPI (endpoints de la API)
    "app/routers": [
        "__init__.py",
        "auth.py",              # Login, registro, JWT
        "usuarios.py",          # CRUD usuarios
        "clientes.py",          # CRUD clientes
        "proveedores.py",       # CRUD proveedores
        "personal.py",          # CRUD personal y roles
        "catalogo.py",          # CRUD categorías, temáticas, servicios
        "paquetes.py",          # CRUD paquetes
        "disponibilidad.py",    # Consulta disponibilidad en tiempo real
        "reservas.py",          # Crear y gestionar reservas
        "pagos.py",             # Procesar pagos y comprobantes
        "notificaciones.py",    # Enviar y leer notificaciones
        "resenas.py",           # Crear y leer reseñas
        "chat.py",              # Endpoint del chat con IA
    ],

    # Servicios (lógica de negocio)
    "app/services": [
        "__init__.py",
        "auth_service.py",          # Autenticación y tokens JWT
        "disponibilidad_service.py",# Consulta disponibilidad real
        "bloqueo_service.py",       # Bloqueo temporal en Redis (10 min)
        "reserva_service.py",       # Lógica de creación de reservas
        "pago_service.py",          # Validación y procesamiento de pagos
        "comprobante_service.py",   # Emisión de comprobantes PDF
        "notificacion_service.py",  # Envío de notificaciones
        "ia_service.py",            # Lógica del asistente virtual IA
    ],

    # Core (seguridad, dependencias, excepciones)
    "app/core": [
        "__init__.py",
        "security.py",      # Hashing de contraseñas, JWT
        "dependencies.py",  # Dependencias inyectables de FastAPI
        "exceptions.py",    # Excepciones personalizadas
    ],

    # Utilidades
    "app/utils": [
        "__init__.py",
        "helpers.py",       # Funciones auxiliares generales
        "validators.py",    # Validaciones de negocio
    ],

    # Migraciones Alembic
    "migrations": ["env.py", "script.py.mako"],
    "migrations/versions": [".gitkeep"],

    # Tests
    "tests": [
        "__init__.py",
        "test_auth.py",
        "test_reservas.py",
        "test_disponibilidad.py",
        "test_pagos.py",
    ],
}

# ── Contenido base para archivos clave ──────────────────────────────────────

contenido_base = {
    "requirements.txt": """\
fastapi==0.111.0
uvicorn[standard]==0.29.0
sqlalchemy==2.0.30
alembic==1.13.1
psycopg2-binary==2.9.9
python-dotenv==1.0.1
passlib[bcrypt]==1.7.4
python-jose[cryptography]==3.3.0
redis==5.0.4
httpx==0.27.0
pydantic[email]==2.7.1
python-multipart==0.0.9
""",

    ".env.example": """\
# Base de datos
DATABASE_URL=postgresql://usuario:contraseña@localhost:5432/festio_db

# Redis
REDIS_URL=redis://localhost:6379

# JWT
SECRET_KEY=cambia_esto_por_una_clave_segura
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# App
APP_NAME=Festio
DEBUG=True
""",

    ".gitignore": """\
__pycache__/
*.pyc
.env
*.egg-info/
.venv/
venv/
dist/
build/
.idea/
.vscode/
*.db
*.sqlite3
""",

    "README.md": """\
# Festio - Backend

API REST para la plataforma Festio.  
Stack: FastAPI · PostgreSQL · Redis · SQLAlchemy · Alembic

## Requisitos
- Python 3.11+
- PostgreSQL
- Redis

## Instalación
```bash
pip install -r requirements.txt
```

## Ejecutar
```bash
uvicorn app.main:app --reload
```

## Documentación automática
- Swagger UI: http://localhost:8000/docs
- ReDoc:       http://localhost:8000/redoc
""",

    "app/main.py": """\
from fastapi import FastAPI
from app.config import settings
from app.routers import (
    auth, usuarios, clientes, proveedores,
    personal, catalogo, paquetes, disponibilidad,
    reservas, pagos, notificaciones, resenas, chat
)

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="API de Festio - Plataforma de reserva de servicios para eventos"
)

# Registrar routers
app.include_router(auth.router,             prefix="/api/auth",             tags=["Autenticación"])
app.include_router(usuarios.router,         prefix="/api/usuarios",         tags=["Usuarios"])
app.include_router(clientes.router,         prefix="/api/clientes",         tags=["Clientes"])
app.include_router(proveedores.router,      prefix="/api/proveedores",      tags=["Proveedores"])
app.include_router(personal.router,         prefix="/api/personal",         tags=["Personal"])
app.include_router(catalogo.router,         prefix="/api/catalogo",         tags=["Catálogo"])
app.include_router(paquetes.router,         prefix="/api/paquetes",         tags=["Paquetes"])
app.include_router(disponibilidad.router,   prefix="/api/disponibilidad",   tags=["Disponibilidad"])
app.include_router(reservas.router,         prefix="/api/reservas",         tags=["Reservas"])
app.include_router(pagos.router,            prefix="/api/pagos",            tags=["Pagos"])
app.include_router(notificaciones.router,   prefix="/api/notificaciones",   tags=["Notificaciones"])
app.include_router(resenas.router,          prefix="/api/resenas",          tags=["Reseñas"])
app.include_router(chat.router,             prefix="/api/chat",             tags=["Chat IA"])

@app.get("/")
def root():
    return {"mensaje": "Bienvenido a la API de Festio 🎉"}
""",

    "app/config.py": """\
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Festio"
    DEBUG: bool = True
    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379"
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    class Config:
        env_file = ".env"

settings = Settings()
""",

    "app/database.py": """\
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
""",

    "app/redis_client.py": """\
import redis
from app.config import settings

# Cliente Redis para bloqueos temporales de inventario
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

BLOQUEO_TTL_SEGUNDOS = 600  # 10 minutos

def bloquear_inventario(reserva_key: str, datos: dict) -> bool:
    \"\"\"Bloquea el inventario por 10 minutos en Redis.\"\"\"
    import json
    return redis_client.setex(
        name=f"bloqueo:{reserva_key}",
        time=BLOQUEO_TTL_SEGUNDOS,
        value=json.dumps(datos)
    )

def liberar_inventario(reserva_key: str) -> bool:
    \"\"\"Libera el bloqueo del inventario manualmente.\"\"\"
    return redis_client.delete(f"bloqueo:{reserva_key}") > 0

def obtener_bloqueo(reserva_key: str) -> dict | None:
    \"\"\"Verifica si existe un bloqueo activo.\"\"\"
    import json
    data = redis_client.get(f"bloqueo:{reserva_key}")
    return json.loads(data) if data else None
""",

    "app/core/security.py": """\
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
""",

    "app/core/dependencies.py": """\
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.security import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar las credenciales",
    )
    try:
        payload = decode_token(token)
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except Exception:
        raise credentials_exception
    return user_id
""",

    "app/core/exceptions.py": """\
from fastapi import HTTPException, status

class DisponibilidadException(HTTPException):
    def __init__(self, detail: str = "No hay disponibilidad para el horario solicitado"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)

class BloqueoExpiradoException(HTTPException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_408_REQUEST_TIMEOUT,
                         detail="El tiempo de bloqueo expiró. Por favor reinicia la reserva.")

class PagoFallidoException(HTTPException):
    def __init__(self, detail: str = "La transacción fue rechazada"):
        super().__init__(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail=detail)
""",
}


def crear_archivo(ruta_completa: str, contenido: str = "") -> None:
    os.makedirs(os.path.dirname(ruta_completa), exist_ok=True)
    if not os.path.exists(ruta_completa):
        with open(ruta_completa, "w", encoding="utf-8") as f:
            f.write(contenido)


def main():
    print(f"\n📁 Creando estructura en: {BASE}\n")

    for carpeta, archivos in estructura.items():
        for archivo in archivos:
            ruta_rel = os.path.join(carpeta, archivo) if carpeta else archivo
            ruta_completa = os.path.join(BASE, ruta_rel.replace("/", os.sep))
            clave = ruta_rel.replace("\\", "/")
            contenido = contenido_base.get(clave, "")
            crear_archivo(ruta_completa, contenido)
            print(f"  ✅ {ruta_rel}")

    print(f"\n🎉 Estructura creada correctamente en {BASE}")
    print("\nSiguiente paso:")
    print("  1. Abre la carpeta en VSCode")
    print("  2. Crea el entorno virtual:  python -m venv venv")
    print("  3. Actívalo:                 venv\\Scripts\\activate")
    print("  4. Instala dependencias:     pip install -r requirements.txt")
    print("  5. Copia .env.example a .env y configura tus credenciales")


if __name__ == "__main__":
    main()

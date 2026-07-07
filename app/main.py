from dotenv import load_dotenv
load_dotenv() # Esto carga el .env antes de que el resto del código despierte
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import (
    auth, usuarios, clientes, proveedores,
    personal, catalogo, paquetes, disponibilidad,
    reservas, pagos, notificaciones, resenas, chat,
    proveedor_inventario, proveedor_paquetes, proveedor_reservas,
)

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from app.core.limiter import limiter

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="API de Festio - Plataforma de reserva de servicios para eventos"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins_list,
    allow_origin_regex=settings.cors_allow_origin_regex_value,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_private_network_cors_header(request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Private-Network"] = "true"
    return response

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

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

# ── Routers B2B (Proveedor autenticado) ──────────────────────────────────────
app.include_router(proveedor_inventario.router, prefix="/api/proveedor/inventario", tags=["Proveedor - Inventario"])
app.include_router(proveedor_paquetes.router,   prefix="/api/proveedor/paquetes",   tags=["Proveedor - Paquetes"])
app.include_router(proveedor_reservas.router, prefix="/api/proveedor/reservas", tags=["Proveedor - Reservas"])

@app.get("/")
def root():
    return {"mensaje": "Bienvenido a la API de Festio "}

import os

base_dir = r'd:\desarrollo-uni\formación-festio'

def rewrite_file(path, old_content, new_content):
    full_path = os.path.join(base_dir, path)
    with open(full_path, 'r', encoding='utf-8') as f:
        content = f.read()
    if content != new_content:
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated {path}")

# 1. Cliente
rewrite_file(r'app\services\cliente_service.py', '', '''from typing import List
from fastapi import HTTPException
from app.domain.usuarios.models import Cliente
from app.domain.usuarios.schemas import ClienteCreate
from app.repositories.usuario_repository import ClienteRepository

def listar_clientes(repo: ClienteRepository) -> List[Cliente]:
    return repo.get_all()

def obtener_cliente(cliente_id: int, repo: ClienteRepository) -> Cliente:
    cliente = repo.get(cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return cliente

def crear_cliente(datos: ClienteCreate, repo: ClienteRepository) -> Cliente:
    return repo.create(datos)
''')

rewrite_file(r'app\routers\clientes.py', '', '''from typing import List
from fastapi import APIRouter, Depends
from app.domain.usuarios.schemas import ClienteCreate, ClienteOut
from app.repositories.usuario_repository import ClienteRepository, get_cliente_repo
from app.services import cliente_service

router = APIRouter()

@router.get("/", response_model=List[ClienteOut])
def listar_clientes(repo: ClienteRepository = Depends(get_cliente_repo)):
    return cliente_service.listar_clientes(repo)

@router.get("/{cliente_id}", response_model=ClienteOut)
def obtener_cliente(cliente_id: int, repo: ClienteRepository = Depends(get_cliente_repo)):
    return cliente_service.obtener_cliente(cliente_id, repo)

@router.post("/", response_model=ClienteOut, status_code=201)
def crear_cliente(datos: ClienteCreate, repo: ClienteRepository = Depends(get_cliente_repo)):
    return cliente_service.crear_cliente(datos, repo)
''')

# 2. Notificacion
rewrite_file(r'app\services\notificacion_service.py', '', '''from typing import List
from fastapi import HTTPException
from app.domain.notificaciones.models import Notificacion
from app.domain.notificaciones.schemas import NotificacionCreate
from app.repositories.notificacion_repository import NotificacionRepository

def listar_notificaciones(repo: NotificacionRepository) -> List[Notificacion]:
    return repo.get_all()

def obtener_notificacion(notificacion_id: int, repo: NotificacionRepository) -> Notificacion:
    notificacion = repo.get(notificacion_id)
    if not notificacion:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")
    return notificacion

def crear_notificacion(datos: NotificacionCreate, repo: NotificacionRepository) -> Notificacion:
    return repo.create(datos)
''')

rewrite_file(r'app\routers\notificaciones.py', '', '''from typing import List
from fastapi import APIRouter, Depends
from app.domain.notificaciones.schemas import NotificacionCreate, NotificacionOut
from app.repositories.notificacion_repository import NotificacionRepository, get_notificacion_repo
from app.services import notificacion_service

router = APIRouter()

@router.get("/", response_model=List[NotificacionOut])
def listar_notificaciones(repo: NotificacionRepository = Depends(get_notificacion_repo)):
    return notificacion_service.listar_notificaciones(repo)

@router.get("/{notificacion_id}", response_model=NotificacionOut)
def obtener_notificacion(notificacion_id: int, repo: NotificacionRepository = Depends(get_notificacion_repo)):
    return notificacion_service.obtener_notificacion(notificacion_id, repo)

@router.post("/", response_model=NotificacionOut, status_code=201)
def crear_notificacion(datos: NotificacionCreate, repo: NotificacionRepository = Depends(get_notificacion_repo)):
    return notificacion_service.crear_notificacion(datos, repo)
''')

# 3. Resena
rewrite_file(r'app\services\resena_service.py', '', '''from typing import List
from fastapi import HTTPException
from app.domain.resenas.models import Resena
from app.domain.resenas.schemas import ResenaCreate
from app.repositories.resena_repository import ResenaRepository

def listar_resenas(repo: ResenaRepository) -> List[Resena]:
    return repo.get_all()

def obtener_resena(resena_id: int, repo: ResenaRepository) -> Resena:
    resena = repo.get(resena_id)
    if not resena:
        raise HTTPException(status_code=404, detail="Reseña no encontrada")
    return resena

def crear_resena(datos: ResenaCreate, repo: ResenaRepository) -> Resena:
    return repo.create(datos)
''')

rewrite_file(r'app\routers\resenas.py', '', '''from typing import List
from fastapi import APIRouter, Depends
from app.domain.resenas.schemas import ResenaCreate, ResenaOut
from app.repositories.resena_repository import ResenaRepository, get_resena_repo
from app.services import resena_service

router = APIRouter()

@router.get("/", response_model=List[ResenaOut])
def listar_resenas(repo: ResenaRepository = Depends(get_resena_repo)):
    return resena_service.listar_resenas(repo)

@router.get("/{resena_id}", response_model=ResenaOut)
def obtener_resena(resena_id: int, repo: ResenaRepository = Depends(get_resena_repo)):
    return resena_service.obtener_resena(resena_id, repo)

@router.post("/", response_model=ResenaOut, status_code=201)
def crear_resena(datos: ResenaCreate, repo: ResenaRepository = Depends(get_resena_repo)):
    return resena_service.crear_resena(datos, repo)
''')

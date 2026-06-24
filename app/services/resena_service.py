from typing import List

from fastapi import HTTPException

from app.domain.resenas.models import Resena
from app.domain.usuarios.models import Proveedor, Usuario
from app.domain.pagos.schemas import ResenaCreate
from app.domain.resenas.schemas import ResenaPublicaCreate, ResenaPublicaOut
from app.repositories.resena_repository import ResenaRepository
from app.repositories.usuario_repository import ProveedorRepository, UsuarioRepository


def listar_resenas_proveedor(proveedor_id: int, repo: ResenaRepository) -> List[Resena]:
    """Lista todas las reseñas de un proveedor."""
    return repo.db.query(Resena).filter(Resena.proveedor_id == proveedor_id).all()


def listar_resenas_publicas(
    proveedor_id: int,
    resena_repo: ResenaRepository,
    usuario_repo: UsuarioRepository,
) -> List[ResenaPublicaOut]:
    """Lista reseñas de un proveedor con el nombre del usuario que la escribió."""
    resenas = (
        resena_repo.db.query(Resena)
        .filter(Resena.proveedor_id == proveedor_id)
        .order_by(Resena.fecha.desc())
        .all()
    )
    resultado: List[ResenaPublicaOut] = []
    for r in resenas:
        nombre = "Usuario"
        if r.usuario_id:
            usuario = usuario_repo.get(r.usuario_id)
            if usuario:
                nombre = f"{usuario.nombre} {usuario.apellido[0]}." if usuario.apellido else usuario.nombre
        elif r.cliente_id:
            from app.domain.usuarios.models import Cliente
            cliente = usuario_repo.db.query(Cliente).filter(Cliente.id == r.cliente_id).first()
            if cliente and cliente.usuario:
                u = cliente.usuario
                nombre = f"{u.nombre} {u.apellido[0]}." if u.apellido else u.nombre

        resultado.append(ResenaPublicaOut(
            id=r.id,
            proveedor_id=r.proveedor_id,
            calificacion=r.calificacion,
            comentario=r.comentario,
            fecha=r.fecha,
            nombre_usuario=nombre,
        ))
    return resultado


def crear_resena_publica(
    datos: ResenaPublicaCreate,
    usuario: Usuario,
    resena_repo: ResenaRepository,
    proveedor_repo: ProveedorRepository
) -> Resena:
    if not (1 <= datos.calificacion <= 5):
        raise HTTPException(
            status_code=400, detail="La calificación debe ser entre 1 y 5"
        )

    proveedor = proveedor_repo.get(datos.proveedor_id)
    if not proveedor:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")

    resena = Resena(
        usuario_id=usuario.id,
        proveedor_id=datos.proveedor_id,
        calificacion=datos.calificacion,
        comentario=datos.comentario,
    )
    resena_repo.db.add(resena)
    resena_repo.db.flush()

    todas = resena_repo.db.query(Resena).filter(Resena.proveedor_id == datos.proveedor_id).all()
    promedio = sum(r.calificacion for r in todas) / len(todas)
    proveedor.calificacion_promedio = round(promedio, 2)

    resena_repo.db.commit()
    resena_repo.db.refresh(resena)
    return resena


def crear_resena(
    datos: ResenaCreate,
    resena_repo: ResenaRepository,
    proveedor_repo: ProveedorRepository
) -> Resena:
    if not (1 <= datos.calificacion <= 5):
        raise HTTPException(
            status_code=400, detail="La calificación debe ser entre 1 y 5"
        )

    resena = Resena(**datos.model_dump())
    resena_repo.db.add(resena)
    resena_repo.db.flush()

    todas = resena_repo.db.query(Resena).filter(Resena.proveedor_id == datos.proveedor_id).all()
    promedio = sum(r.calificacion for r in todas) / len(todas)

    proveedor = proveedor_repo.get(datos.proveedor_id)
    if proveedor:
        proveedor.calificacion_promedio = round(promedio, 2)

    resena_repo.db.commit()
    resena_repo.db.refresh(resena)
    return resena

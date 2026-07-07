from typing import List

from fastapi import HTTPException
from sqlalchemy import or_

from app.domain.resenas.models import Resena
from app.domain.usuarios.models import Usuario
from app.domain.pagos.schemas import ResenaCreate
from app.domain.resenas.schemas import ResenaPublicaCreate, ResenaPublicaOut
from app.repositories.resena_repository import ResenaRepository
from app.repositories.usuario_repository import ProveedorRepository, UsuarioRepository


_MENSAJE_RESENA_DUPLICADA = "Ya dejaste una reseña para este proveedor"


def _validar_resena_unica(usuario: Usuario, proveedor_id: int, resena_repo: ResenaRepository) -> None:
    filtros_usuario = [Resena.usuario_id == usuario.id]

    cliente = getattr(usuario, "cliente", None)
    if cliente is not None:
        filtros_usuario.append(Resena.cliente_id == cliente.id)

    resena_existente = (
        resena_repo.db.query(Resena)
        .filter(
            Resena.proveedor_id == proveedor_id,
            or_(*filtros_usuario),
        )
        .first()
    )
    if resena_existente:
        raise HTTPException(status_code=409, detail=_MENSAJE_RESENA_DUPLICADA)


def listar_resenas_proveedor(proveedor_id: int, repo: ResenaRepository) -> List[Resena]:
    """Lista todas las reseñas de un proveedor."""
    return repo.db.query(Resena).filter(Resena.proveedor_id == proveedor_id).all()


def listar_resenas_publicas(
    proveedor_id: int,
    resena_repo: ResenaRepository,
    usuario_repo: UsuarioRepository,
    skip: int = 0,
    limit: int = 100,
) -> List[ResenaPublicaOut]:
    resenas = (
        resena_repo.db.query(Resena)
        .filter(Resena.proveedor_id == proveedor_id)
        .order_by(Resena.fecha.desc())
        .offset(skip)
        .limit(limit)
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
    proveedor = proveedor_repo.get(datos.proveedor_id)
    if not proveedor:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")

    _validar_resena_unica(usuario, datos.proveedor_id, resena_repo)

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
    usuario: Usuario,
    resena_repo: ResenaRepository,
    proveedor_repo: ProveedorRepository
) -> Resena:
    _validar_resena_unica(usuario, datos.proveedor_id, resena_repo)

    resena = Resena(**datos.model_dump(), usuario_id=usuario.id)
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

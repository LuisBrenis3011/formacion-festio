from typing import List

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.resena import Resena
from app.models.usuario import Proveedor, Usuario
from app.schemas.pago import ResenaCreate
from app.schemas.resena import ResenaPublicaCreate, ResenaPublicaOut


def listar_resenas_proveedor(proveedor_id: int, db: Session) -> List[Resena]:
    """Lista todas las reseñas de un proveedor."""
    return db.query(Resena).filter(Resena.proveedor_id == proveedor_id).all()


def listar_resenas_publicas(proveedor_id: int, db: Session) -> List[ResenaPublicaOut]:
    """Lista reseñas de un proveedor con el nombre del usuario que la escribió."""
    resenas = (
        db.query(Resena)
        .filter(Resena.proveedor_id == proveedor_id)
        .order_by(Resena.fecha.desc())
        .all()
    )
    resultado: List[ResenaPublicaOut] = []
    for r in resenas:
        # Obtener nombre del usuario (por usuario_id directo o por cliente_id)
        nombre = "Usuario"
        if r.usuario_id:
            usuario = db.query(Usuario).filter(Usuario.id == r.usuario_id).first()
            if usuario:
                nombre = f"{usuario.nombre} {usuario.apellido[0]}." if usuario.apellido else usuario.nombre
        elif r.cliente_id:
            from app.models.usuario import Cliente
            cliente = db.query(Cliente).filter(Cliente.id == r.cliente_id).first()
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


def crear_resena_publica(datos: ResenaPublicaCreate, usuario: Usuario, db: Session) -> Resena:
    """
    Crea una reseña pública (sin reserva asociada).
    El usuario autenticado queda vinculado directamente.
    """
    if not (1 <= datos.calificacion <= 5):
        raise HTTPException(
            status_code=400, detail="La calificación debe ser entre 1 y 5"
        )

    # Verificar que el proveedor existe
    proveedor = db.query(Proveedor).filter(Proveedor.id == datos.proveedor_id).first()
    if not proveedor:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")

    resena = Resena(
        usuario_id=usuario.id,
        proveedor_id=datos.proveedor_id,
        calificacion=datos.calificacion,
        comentario=datos.comentario,
    )
    db.add(resena)
    db.flush()

    # Recalcular el promedio del proveedor
    todas = db.query(Resena).filter(Resena.proveedor_id == datos.proveedor_id).all()
    promedio = sum(r.calificacion for r in todas) / len(todas)
    proveedor.calificacion_promedio = round(promedio, 2)

    db.commit()
    db.refresh(resena)
    return resena


def crear_resena(datos: ResenaCreate, db: Session) -> Resena:
    """
    El cliente deja su reseña después de completar el evento.
    Valida la calificación y recalcula el promedio del proveedor.
    """
    if not (1 <= datos.calificacion <= 5):
        raise HTTPException(
            status_code=400, detail="La calificación debe ser entre 1 y 5"
        )

    resena = Resena(**datos.model_dump())
    db.add(resena)
    db.flush()

    # Recalcular el promedio del proveedor
    todas = db.query(Resena).filter(Resena.proveedor_id == datos.proveedor_id).all()
    promedio = sum(r.calificacion for r in todas) / len(todas)

    proveedor = db.query(Proveedor).filter(Proveedor.id == datos.proveedor_id).first()
    if proveedor:
        proveedor.calificacion_promedio = round(promedio, 2)

    db.commit()
    db.refresh(resena)
    return resena

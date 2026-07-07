from typing import List

from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.domain.resenas.models import Resena
from app.domain.reservas.models import Reserva, Evento
from app.domain.usuarios.models import Cliente, Usuario
from app.domain.pagos.schemas import ResenaCreate, ResenaUpdate
from app.domain.resenas.schemas import ResenaPublicaCreate, ResenaPublicaOut
from app.repositories.resena_repository import ResenaRepository
from app.repositories.usuario_repository import ProveedorRepository, UsuarioRepository

from sqlalchemy import func
from app.domain.reservas.models import Reserva, DetalleReserva
from app.domain.catalogo.models import Paquete
from app.domain.common.enums import EstadoReserva
from app.domain.usuarios.models import Proveedor
from app.repositories.reserva_repository import ReservaRepository
from app.domain.resenas.schemas import TopPaqueteOut, ResenaRecienteOut, MarketAnalyticsOut

_MENSAJE_RESENA_DUPLICADA = "Ya dejaste una reseña para esta reserva"
_MENSAJE_RESENA_DUPLICADA_PROVEEDOR = "Ya dejaste una reseña para este proveedor"
_MENSAJE_RESENA_NO_ENCONTRADA = "Reseña no encontrada"
_MENSAJE_RESENA_NO_AUTORIZADA = "Solo puedes editar tus propias reseñas"


def _recalcular_promedio_proveedor(proveedor_id: int, db: Session) -> None:
    from app.domain.usuarios.models import Proveedor
    todas = db.query(Resena).filter(Resena.proveedor_id == proveedor_id).all()
    promedio = round(sum(r.calificacion for r in todas) / len(todas), 2) if todas else 0.00
    proveedor = db.query(Proveedor).filter(Proveedor.id == proveedor_id).first()
    if proveedor:
        proveedor.calificacion_promedio = promedio


def _validar_reserva_pertenece_usuario(reserva_id: int, usuario: Usuario, db: Session) -> Reserva:
    reserva = db.query(Reserva).filter(Reserva.id == reserva_id).first()
    if not reserva:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")

    cliente = db.query(Cliente).filter(Cliente.id == reserva.evento.cliente_id).first()
    if not cliente or cliente.usuario_id != usuario.id:
        raise HTTPException(status_code=403, detail="Esta reserva no te pertenece")

    return reserva


def _validar_resena_por_reserva(usuario: Usuario, reserva_id: int, resena_repo: ResenaRepository) -> None:
    filtros_usuario = [Resena.usuario_id == usuario.id]

    cliente = getattr(usuario, "cliente", None)
    if cliente is not None:
        filtros_usuario.append(Resena.cliente_id == cliente.id)

    resena_existente = (
        resena_repo.db.query(Resena)
        .filter(
            Resena.reserva_id == reserva_id,
            or_(*filtros_usuario),
        )
        .first()
    )
    if resena_existente:
        raise HTTPException(status_code=409, detail=_MENSAJE_RESENA_DUPLICADA)


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
        raise HTTPException(status_code=409, detail=_MENSAJE_RESENA_DUPLICADA_PROVEEDOR)


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

    _recalcular_promedio_proveedor(datos.proveedor_id, resena_repo.db)

    resena_repo.db.commit()
    resena_repo.db.refresh(resena)
    return resena


def crear_resena(
    datos: ResenaCreate,
    usuario: Usuario,
    resena_repo: ResenaRepository,
    proveedor_repo: ProveedorRepository
) -> Resena:
    _validar_reserva_pertenece_usuario(datos.reserva_id, usuario, resena_repo.db)
    _validar_resena_por_reserva(usuario, datos.reserva_id, resena_repo)

    resena = Resena(**datos.model_dump(), usuario_id=usuario.id)
    resena_repo.db.add(resena)
    resena_repo.db.flush()

    _recalcular_promedio_proveedor(datos.proveedor_id, resena_repo.db)

    resena_repo.db.commit()
    resena_repo.db.refresh(resena)
    return resena


def _nombre_resena(r: Resena) -> str:
    if r.usuario_id and r.usuario:
        return f"{r.usuario.nombre} {r.usuario.apellido[0]}." if r.usuario.apellido else r.usuario.nombre
    if r.cliente_id and r.cliente and r.cliente.usuario:
        u = r.cliente.usuario
        return f"{u.nombre} {u.apellido[0]}." if u.apellido else u.nombre
    return "Usuario"


def obtener_market_analytics(
    proveedor: Proveedor,
    resena_repo: ResenaRepository,
    reserva_repo: ReservaRepository,
) -> MarketAnalyticsOut:
    resenas = (
        resena_repo.db.query(Resena)
        .filter(Resena.proveedor_id == proveedor.id)
        .order_by(Resena.fecha.desc())
        .all()
    )

    total_resenas = len(resenas)
    distribucion = {i: 0 for i in range(1, 6)}
    for r in resenas:
        if r.calificacion in distribucion:
            distribucion[r.calificacion] += 1

    resenas_recientes = [
        ResenaRecienteOut(
            id=r.id,
            cliente_nombre=_nombre_resena(r),
            calificacion=r.calificacion,
            comentario=r.comentario,
            fecha=r.fecha,
        )
        for r in resenas[:5]
    ]

    ventas_query = (
        reserva_repo.db.query(
            DetalleReserva.paquete_id,
            Paquete.nombre,
            func.count(DetalleReserva.id).label("ventas"),
        )
        .join(Reserva, Reserva.id == DetalleReserva.reserva_id)
        .join(Paquete, Paquete.id == DetalleReserva.paquete_id)
        .filter(
            Reserva.proveedor_id == proveedor.id,
            DetalleReserva.paquete_id.isnot(None),
            DetalleReserva.deleted_at.is_(None),
            Reserva.deleted_at.is_(None),
            Reserva.estado.in_([EstadoReserva.CONFIRMADA, EstadoReserva.COMPLETADA]),
        )
        .group_by(DetalleReserva.paquete_id, Paquete.nombre)
        .order_by(func.count(DetalleReserva.id).desc())
        .limit(3)
        .all()
    )

    max_ventas = ventas_query[0].ventas if ventas_query else 1
    top_paquetes = [
        TopPaqueteOut(
            paquete_id=pid,
            nombre=nombre,
            ventas=v,
            porcentaje=round((v / max_ventas) * 100, 1) if max_ventas > 0 else 0,
        )
        for pid, nombre, v in ventas_query
    ]

    return MarketAnalyticsOut(
        calificacion_promedio=proveedor.calificacion_promedio or 0.0,
        total_resenas=total_resenas,
        distribucion_estrellas=distribucion,
        top_paquetes=top_paquetes,
        resenas_recientes=resenas_recientes,
    )


def actualizar_resena(
    resena_id: int,
    datos: ResenaUpdate,
    usuario: Usuario,
    resena_repo: ResenaRepository,
    proveedor_repo: ProveedorRepository,
) -> Resena:
    resena = resena_repo.get(resena_id)
    if not resena:
        raise HTTPException(status_code=404, detail=_MENSAJE_RESENA_NO_ENCONTRADA)

    if resena.usuario_id != usuario.id:
        cliente = getattr(usuario, "cliente", None)
        if not cliente or resena.cliente_id != cliente.id:
            raise HTTPException(status_code=403, detail=_MENSAJE_RESENA_NO_AUTORIZADA)

    update_data = datos.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="Al menos un campo debe enviarse (calificacion o comentario)")

    for campo, valor in update_data.items():
        setattr(resena, campo, valor)

    resena_repo.db.flush()
    _recalcular_promedio_proveedor(resena.proveedor_id, resena_repo.db)
    resena_repo.db.commit()
    resena_repo.db.refresh(resena)
    return resena
from typing import List, Optional

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_current_user, get_optional_current_user
from app.domain.usuarios.models import Usuario
from app.domain.reservas.schemas import (
    CheckoutClienteCreate,
    CheckoutReservaResponse,
    EventoCreate,
    EventoOut,
    MisReservasItemOut,
    PreReservaCreate,
    PreReservaResponse,
    ReservaCreate,
    ReservaOut,
)
from app.services.reserva import evento_service, checkout_service, reserva_gestion_service
from app.repositories.usuario_repository import get_proveedor_repo, get_cliente_repo, get_usuario_repo
from app.repositories.catalogo_repository import get_paquete_repo, get_servicio_producto_repo, get_detalle_paquete_repo
from app.repositories.reserva_repository import get_evento_repo, get_reserva_repo, get_detalle_reserva_repo
from app.repositories.pago_repository import get_pago_transaccion_repo
from app.repositories.disponibilidad_repository import get_ocupacion_servicio_producto_repo, get_ocupacion_global_proveedor_repo

from pydantic import BaseModel, Field
from app.core.dependencies import get_current_user, get_optional_current_user, get_current_proveedor
from app.domain.usuarios.models import Usuario, Proveedor
from app.domain.common.enums import MetodoPago
from app.repositories.pago_repository import get_pago_transaccion_repo

router = APIRouter()


# ── Eventos ───────────────────────────────────────────────────────────────────

@router.post("/eventos", response_model=EventoOut, status_code=201)
def crear_evento(
    datos: EventoCreate,
    evento_repo = Depends(get_evento_repo),
    _: int = Depends(get_current_user)
):
    """Crea el evento base del cliente antes de agregar reservas."""
    return evento_service.crear_evento(datos, evento_repo)


@router.get("/eventos/{evento_id}", response_model=EventoOut)
def obtener_evento(evento_id: int, evento_repo = Depends(get_evento_repo)):
    return evento_service.obtener_evento(evento_id, evento_repo)


@router.get("/cliente/{cliente_id}", response_model=List[EventoOut])
def eventos_por_cliente(
    cliente_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    evento_repo = Depends(get_evento_repo),
):
    return evento_service.eventos_por_cliente(cliente_id, evento_repo, skip=skip, limit=limit)


# ── Reservas ──────────────────────────────────────────────────────────────────

@router.post("/prebloquear", response_model=PreReservaResponse)
def prebloquear_reserva(
    datos: PreReservaCreate,
    proveedor_repo = Depends(get_proveedor_repo),
    paquete_repo = Depends(get_paquete_repo),
    servicio_repo = Depends(get_servicio_producto_repo),
    detalle_paquete_repo = Depends(get_detalle_paquete_repo),
    ocupacion_sp_repo = Depends(get_ocupacion_servicio_producto_repo),
    ocupacion_global_repo = Depends(get_ocupacion_global_proveedor_repo),
):
    """
    Flujo público: bloquea paquete y adicionales por 10 minutos.
    Aún no crea usuario, evento ni reserva definitiva.
    """
    return checkout_service.prebloquear_reserva(
        datos, proveedor_repo, paquete_repo, servicio_repo, detalle_paquete_repo, ocupacion_sp_repo, ocupacion_global_repo
    )


@router.post("/checkout-simulado/{reserva_temp_id}", response_model=CheckoutReservaResponse)
def checkout_simulado(
    reserva_temp_id: str,
    datos: CheckoutClienteCreate,
    usuario: Optional[Usuario] = Depends(get_optional_current_user),
    cliente_repo = Depends(get_cliente_repo),
    usuario_repo = Depends(get_usuario_repo),
    proveedor_repo = Depends(get_proveedor_repo),
    servicio_repo = Depends(get_servicio_producto_repo),
    ocupacion_sp_repo = Depends(get_ocupacion_servicio_producto_repo),
    ocupacion_global_repo = Depends(get_ocupacion_global_proveedor_repo),
    evento_repo = Depends(get_evento_repo),
    reserva_repo = Depends(get_reserva_repo),
    detalle_reserva_repo = Depends(get_detalle_reserva_repo),
    pago_repo = Depends(get_pago_transaccion_repo),
):
    """
    Flujo público: registra/reusa cliente, simula pago aprobado del 10%
    y convierte el bloqueo temporal en una reserva confirmada.
    """
    return checkout_service.confirmar_checkout_simulado(
        reserva_temp_id, datos, usuario, cliente_repo, usuario_repo, proveedor_repo,
        servicio_repo, ocupacion_sp_repo, ocupacion_global_repo, evento_repo,
        reserva_repo, detalle_reserva_repo, pago_repo
    )


@router.post("/iniciar", status_code=200)
def iniciar_reserva(
    datos: ReservaCreate,
    evento_repo = Depends(get_evento_repo),
    paquete_repo = Depends(get_paquete_repo),
    servicio_repo = Depends(get_servicio_producto_repo),
    _: int = Depends(get_current_user)
):
    """
    PASO 1 del flujo principal.
    Valida disponibilidad y crea el bloqueo temporal en Redis (10 min).
    Retorna el reserva_temp_id y los montos calculados.
    No escribe nada en la BD todavía.
    """
    return checkout_service.iniciar_reserva(datos, evento_repo, paquete_repo, servicio_repo)


@router.post("/confirmar/{reserva_temp_id}", response_model=ReservaOut)
def confirmar_reserva(
    reserva_temp_id: str,
    pago_id: int,
    evento_repo = Depends(get_evento_repo),
    reserva_repo = Depends(get_reserva_repo),
    detalle_reserva_repo = Depends(get_detalle_reserva_repo),
    servicio_repo = Depends(get_servicio_producto_repo),
    ocupacion_sp_repo = Depends(get_ocupacion_servicio_producto_repo),
    ocupacion_global_repo = Depends(get_ocupacion_global_proveedor_repo),
    _: int = Depends(get_current_user)
):
    """
    PASO 2 del flujo principal.
    Llamado solo después de validar el pago exitoso.
    Convierte el bloqueo temporal en reserva definitiva en la BD.
    """
    return checkout_service.confirmar_reserva(
        reserva_temp_id, pago_id, evento_repo, reserva_repo, detalle_reserva_repo,
        servicio_repo, ocupacion_sp_repo, ocupacion_global_repo
    )


@router.get("/mis-reservas", response_model=List[MisReservasItemOut])
def mis_reservas(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    usuario: Usuario = Depends(get_current_user),
    reserva_repo = Depends(get_reserva_repo),
    evento_repo = Depends(get_evento_repo),
    cliente_repo = Depends(get_cliente_repo),
    proveedor_repo = Depends(get_proveedor_repo),
    paquete_repo = Depends(get_paquete_repo),
    servicio_repo = Depends(get_servicio_producto_repo),
):
    return reserva_gestion_service.listar_mis_reservas(
        usuario, reserva_repo, evento_repo, cliente_repo, proveedor_repo, paquete_repo, servicio_repo,
        skip=skip, limit=limit,
    )


@router.get("/{reserva_id}", response_model=ReservaOut)
def obtener_reserva(reserva_id: int, reserva_repo = Depends(get_reserva_repo)):
    return reserva_gestion_service.obtener_reserva(reserva_id, reserva_repo)


@router.patch("/{reserva_id}/cancelar", status_code=200)
def cancelar_reserva(
    reserva_id: int,
    reserva_repo = Depends(get_reserva_repo),
    usuario: Usuario = Depends(get_current_user),
):
    """Cancela una reserva confirmada sin ocultarla del historial."""
    return reserva_gestion_service.cancelar_reserva(reserva_id, usuario, reserva_repo)

class CompletarReservaRequest(BaseModel):
    metodo_pago: MetodoPago = MetodoPago.EFECTIVO
    codigo_transaccion: Optional[str] = Field(None, max_length=150)


class CompletarReservaResponse(BaseModel):
    reserva_id: int
    estado: str
    pago_id: int
    monto_pagado: float
    mensaje: str


@router.patch("/{reserva_id}/completar", response_model=CompletarReservaResponse)
def completar_reserva(
    reserva_id: int,
    datos: CompletarReservaRequest,
    proveedor: Proveedor = Depends(get_current_proveedor),
    reserva_repo = Depends(get_reserva_repo),
    pago_repo = Depends(get_pago_transaccion_repo),
):
    """Solo el proveedor dueño puede marcar su reserva como completada."""
    return reserva_gestion_service.completar_reserva(
        reserva_id, datos.metodo_pago, datos.codigo_transaccion, proveedor, reserva_repo, pago_repo
    )
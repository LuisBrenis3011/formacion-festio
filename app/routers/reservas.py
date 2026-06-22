from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_optional_current_user
from app.database import get_db
from app.models.usuario import Usuario
from app.schemas.reserva import (
    CheckoutClienteCreate,
    CheckoutReservaResponse,
    EventoCreate,
    EventoOut,
    PreReservaCreate,
    PreReservaResponse,
    ReservaCreate,
    ReservaOut,
)
from app.services import reserva_service

router = APIRouter()


# ── Eventos ───────────────────────────────────────────────────────────────────

@router.post("/eventos", response_model=EventoOut, status_code=201)
def crear_evento(
    datos: EventoCreate,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user)
):
    """Crea el evento base del cliente antes de agregar reservas."""
    return reserva_service.crear_evento(datos, db)


@router.get("/eventos/{evento_id}", response_model=EventoOut)
def obtener_evento(evento_id: int, db: Session = Depends(get_db)):
    return reserva_service.obtener_evento(evento_id, db)


@router.get("/cliente/{cliente_id}", response_model=List[EventoOut])
def eventos_por_cliente(cliente_id: int, db: Session = Depends(get_db)):
    """Historial de eventos de un cliente."""
    return reserva_service.eventos_por_cliente(cliente_id, db)


# ── Reservas ──────────────────────────────────────────────────────────────────

@router.post("/prebloquear", response_model=PreReservaResponse)
def prebloquear_reserva(
    datos: PreReservaCreate,
    db: Session = Depends(get_db),
):
    """
    Flujo público: bloquea paquete y adicionales por 10 minutos.
    Aún no crea usuario, evento ni reserva definitiva.
    """
    return reserva_service.prebloquear_reserva(datos, db)


@router.post("/checkout-simulado/{reserva_temp_id}", response_model=CheckoutReservaResponse)
def checkout_simulado(
    reserva_temp_id: str,
    datos: CheckoutClienteCreate,
    db: Session = Depends(get_db),
    usuario: Optional[Usuario] = Depends(get_optional_current_user),
):
    """
    Flujo público: registra/reusa cliente, simula pago aprobado del 10%
    y convierte el bloqueo temporal en una reserva confirmada.
    """
    return reserva_service.confirmar_checkout_simulado(reserva_temp_id, datos, db, usuario)


@router.post("/iniciar", status_code=200)
def iniciar_reserva(
    datos: ReservaCreate,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user)
):
    """
    PASO 1 del flujo principal.
    Valida disponibilidad y crea el bloqueo temporal en Redis (10 min).
    Retorna el reserva_temp_id y los montos calculados.
    No escribe nada en la BD todavía.
    """
    return reserva_service.iniciar_reserva(datos, db)


@router.post("/confirmar/{reserva_temp_id}", response_model=ReservaOut)
def confirmar_reserva(
    reserva_temp_id: str,
    pago_id: int,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user)
):
    """
    PASO 2 del flujo principal.
    Llamado solo después de validar el pago exitoso.
    Convierte el bloqueo temporal en reserva definitiva en la BD.
    """
    return reserva_service.confirmar_reserva(reserva_temp_id, pago_id, db)


@router.get("/{reserva_id}", response_model=ReservaOut)
def obtener_reserva(reserva_id: int, db: Session = Depends(get_db)):
    return reserva_service.obtener_reserva(reserva_id, db)


@router.patch("/{reserva_id}/cancelar", status_code=200)
def cancelar_reserva(
    reserva_id: int,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user)
):
    """Cancela una reserva confirmada (soft delete)."""
    return reserva_service.cancelar_reserva(reserva_id, db)

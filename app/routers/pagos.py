from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
import logging

from app.core.dependencies import get_current_user
from app.database import get_db
from app.domain.usuarios.models import Usuario
from app.domain.pagos.schemas import PagoCreate, PagoOut, ComprobanteOut
from app.services import pago_service

logger = logging.getLogger(__name__)

router = APIRouter()


class IniciarPagoMP(BaseModel):
    pago: PagoCreate
    titulo_evento: str
    reserva_temp_id: str


@router.post("/iniciar", status_code=200)
def iniciar_pago(
    request_data: IniciarPagoMP,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(get_current_user),
):
    email_cliente = usuario_actual.email

    url_pago = pago_service.iniciar_pago_mercadopago(
        datos=request_data.pago,
        email_cliente=email_cliente,
        titulo_evento=request_data.titulo_evento,
        reserva_temp_id=request_data.reserva_temp_id,
        db=db,
    )

    return {"url_pago": url_pago}

@router.post("/webhook")
async def webhook_mercadopago(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Webhook oficial para Mercado Pago.
    Se ejecuta automáticamente de servidor a servidor sin intervención del frontend.
    """
    try:
        payload = await request.json()
        pago_service.procesar_webhook_mercadopago(payload, db)
        return {"status": "ok"}
    except Exception:
        logger.exception("Error procesando webhook de Mercado Pago")
        return {"status": "received_with_errors"}


@router.post("/{pago_id}/rechazar_manual", response_model=dict)
def rechazar_pago_manual(
    pago_id: int,
    reserva_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(get_current_user),
):
    return pago_service.rechazar_pago_completo(pago_id, usuario_actual.id, reserva_id, db)


@router.get("/comprobante/{reserva_id}", response_model=ComprobanteOut)
def obtener_comprobante(
    reserva_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(get_current_user),
):
    return pago_service.obtener_comprobante(reserva_id, db)
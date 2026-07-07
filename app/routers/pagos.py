from fastapi import APIRouter, Depends, Request, Header, HTTPException, status
from sqlalchemy.orm import Session
import logging

from app.config import settings
from app.core.dependencies import get_current_user
from app.database import get_db
from app.domain.usuarios.models import Usuario
from app.domain.pagos.schemas import PagoCreate, PagoOut, ComprobanteOut, IniciarPagoMPRequest, IniciarPagoMPResponse
from app.services import pago_service
from app.repositories.pago_repository import PagoTransaccionRepository
from app.repositories.reserva_repository import ReservaRepository

logger = logging.getLogger(__name__)

router = APIRouter()


def require_payment_webhook_secret(
    x_webhook_secret: str | None = Header(default=None, alias="X-Webhook-Secret"),
):
    # Este webhook no usa JWT; se protege con un secreto compartido inyectado por entorno.
    if x_webhook_secret != settings.PAYMENT_WEBHOOK_SECRET:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook secret",
        )


@router.post("/iniciar", status_code=200, response_model=IniciarPagoMPResponse)
def iniciar_pago(
    request_data: IniciarPagoMPRequest,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(get_current_user),
):
    url_pago = pago_service.iniciar_pago_mercadopago(
        datos=request_data,
        email_cliente=usuario_actual.email,
        usuario_id=usuario_actual.id,
        db=db,
    )

    return {"url_pago": url_pago}


@router.post("/", response_model=PagoOut, status_code=201)
def registrar_pago(
    datos: PagoCreate,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(get_current_user),
):
    """Registra el intento de pago del adelanto del 10%."""
    pago_repo = PagoTransaccionRepository(db)
    reserva_repo = ReservaRepository(db)

    return pago_service.procesar_pago(
        datos,
        pago_repo,
        reserva_repo
    )


@router.post("/{pago_id}/aprobar", response_model=PagoOut)
def aprobar_pago(
    pago_id: int,
    reserva_temp_id: str,
    codigo_transaccion: str,
    _: None = Depends(require_payment_webhook_secret),
    db: Session = Depends(get_db)
):
    """
    Webhook llamado por la pasarela de pagos al confirmar la transacción.
    1. Aprueba el pago
    2. Confirma la reserva definitiva en BD
    3. Emite el comprobante automáticamente
    4. Notifica a cliente y proveedor en paralelo
    """
    return pago_service.aprobar_pago_completo(
        pago_id, reserva_temp_id, codigo_transaccion, db
    )


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


@router.post("/{pago_id}/rechazar")
def rechazar_pago(
    pago_id: int,
    usuario_id: int,
    reserva_id: int,
    _: None = Depends(require_payment_webhook_secret),
    db: Session = Depends(get_db)
):
    return pago_service.rechazar_pago_completo(pago_id, usuario_id, reserva_id, db)


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
    """Retorna el comprobante de una reserva confirmada."""
    return pago_service.obtener_comprobante(reserva_id, db)
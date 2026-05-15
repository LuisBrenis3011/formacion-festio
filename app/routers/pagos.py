from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database import get_db
from app.schemas.pago import PagoCreate, PagoOut, ComprobanteOut
from app.services import pago_service

router = APIRouter()


@router.post("/", response_model=PagoOut, status_code=201)
def registrar_pago(
    datos: PagoCreate,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user)
):
    """Registra el intento de pago del adelanto del 10%."""
    return pago_service.procesar_pago(datos, db)


@router.post("/{pago_id}/aprobar", response_model=PagoOut)
def aprobar_pago(
    pago_id: int,
    reserva_temp_id: str,
    codigo_transaccion: str,
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


@router.post("/{pago_id}/rechazar")
def rechazar_pago(
    pago_id: int,
    usuario_id: int,
    reserva_id: int,
    db: Session = Depends(get_db)
):
    """Marca el pago como rechazado y notifica al cliente."""
    return pago_service.rechazar_pago_completo(pago_id, usuario_id, reserva_id, db)


@router.get("/comprobante/{reserva_id}", response_model=ComprobanteOut)
def obtener_comprobante(reserva_id: int, db: Session = Depends(get_db)):
    """Retorna el comprobante de una reserva confirmada."""
    return pago_service.obtener_comprobante(reserva_id, db)
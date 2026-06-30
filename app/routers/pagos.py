from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.dependencies import get_current_user
from app.database import get_db
from app.domain.pagos.schemas import PagoCreate, PagoOut, ComprobanteOut
from app.services import pago_service

# Instanciamos el router (asegúrate de registrarlo en main.py con su prefijo, ej: /pagos)
router = APIRouter()

# ─── ESQUEMA AUXILIAR ────────────────────────────────────────────────────────
class IniciarPagoMP(BaseModel):
    pago: PagoCreate
    titulo_evento: str
    reserva_temp_id: str

# ─── ENDPOINTS ───────────────────────────────────────────────────────────────

# ===================================================================
# 🚀 BYPASS TEMPORAL PARA PROBAR MERCADO PAGO SIN BASE DE DATOS
# ===================================================================
@router.post("/iniciar", status_code=200)
def iniciar_pago(request_data: IniciarPagoMP):
    from app.services.mercadopago_service import mp_client
    
    # Llamamos directo a Mercado Pago con datos ficticios
    url_pago = mp_client.generar_preferencia(
        pago_id=9999,  # ID falso para que no busque en BD
        monto=request_data.pago.monto,
        titulo_evento=request_data.titulo_evento,
        email_cliente="cliente_test@festio.com",
        reserva_temp_id=request_data.reserva_temp_id
    )
    return {"url_pago": url_pago}
# ===================================================================

@router.post("/iniciar", status_code=200)
def iniciar_pago(
    request_data: IniciarPagoMP,
    db: Session = Depends(get_db),
    usuario_actual: dict = Depends(get_current_user)  # Asumiendo que retorna un dict o modelo de usuario
):
    """
    Inicia el flujo de pago con Mercado Pago.
    1. Guarda el pago en BD con estado PENDIENTE.
    2. Genera la preferencia en Mercado Pago.
    3. Devuelve la URL (init_point) para que el frontend redirija al cliente.
    """
    # Extraemos el email del usuario autenticado. 
    # (Ajusta la clave 'email' según cómo devuelva los datos tu get_current_user)
    email_cliente = usuario_actual.get("email") if isinstance(usuario_actual, dict) else getattr(usuario_actual, "email", "sin_correo@festio.com")

    url_pago = pago_service.iniciar_pago_mercadopago(
        datos=request_data.pago,
        email_cliente=email_cliente,
        titulo_evento=request_data.titulo_evento,
        reserva_temp_id=request_data.reserva_temp_id,
        db=db
    )
    
    # El frontend usará esta URL para abrir el popup o redirigir
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
        # Obtenemos el payload crudo que envía Mercado Pago
        payload = await request.json()
        
        # Le pasamos la pelota al servicio para que orqueste la BD y las notificaciones
        pago_service.procesar_webhook_mercadopago(payload, db)
        
        # Mercado Pago exige que respondamos con un status 200 rápido
        return {"status": "ok"}
    except Exception as e:
        # Imprimimos el error para depuración en el servidor
        print(f"⚠️ Error procesando webhook de MP: {str(e)}")
        # Seguimos devolviendo 200 para que MP no reintente peticiones fallidas infinitamente
        return {"status": "received_with_errors"}


@router.post("/{pago_id}/rechazar_manual", response_model=dict)
def rechazar_pago_manual(
    pago_id: int,
    reserva_id: int,
    db: Session = Depends(get_db),
    usuario_actual: dict = Depends(get_current_user)
):
    """
    Endpoint de respaldo (Backoffice/Admin).
    Permite marcar un pago como rechazado manualmente si hay incidencias.
    """
    # Obtenemos el ID del usuario para enviarle la notificación de fallo
    usuario_id = usuario_actual.get("id") if isinstance(usuario_actual, dict) else getattr(usuario_actual, "id")
    
    return pago_service.rechazar_pago_completo(pago_id, usuario_id, reserva_id, db)


@router.get("/comprobante/{reserva_id}", response_model=ComprobanteOut)
def obtener_comprobante(reserva_id: int, db: Session = Depends(get_db)):
    """Retorna el comprobante fiscal de una reserva confirmada."""
    return pago_service.obtener_comprobante(reserva_id, db)
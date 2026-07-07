import mercadopago
from app.config import settings


class MercadoPagoError(Exception):
    """Excepción controlada para errores del SDK de Mercado Pago."""


class MercadoPagoClient:
    def __init__(self):
        self.sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)

    def generar_preferencia(
        self,
        external_reference: str,
        monto: float,
        titulo_evento: str,
        email_cliente: str,
        reserva_temp_id: str,
        usuario_id: int,
        metodo_pago: str = "TARJETA",
    ) -> str:
        frontend = settings.FRONTEND_URL.rstrip("/")

        preference_data = {
            "items": [
                {
                    "id": external_reference,
                    "title": titulo_evento,
                    "quantity": 1,
                    "unit_price": float(monto),
                    "currency_id": "PEN",
                }
            ],
            "payer": {
                "email": email_cliente,
            },
            "back_urls": {
                "success": f"{frontend}/pago-exitoso",
                "failure": f"{frontend}/pago-fallido",
                "pending": f"{frontend}/pago-pendiente",
            },
            "auto_return": "approved",
            "external_reference": external_reference,
            "metadata": {
                "reserva_temp_id": reserva_temp_id,
                "usuario_id": usuario_id,
                "metodo_pago": metodo_pago,
            },
        }

        response = self.sdk.preference().create(preference_data)

        if response["status"] != 201:
            raise MercadoPagoError(
                f"Error en Mercado Pago (status {response['status']}): {response['response']}"
            )

        return response["response"]["init_point"]

    def obtener_pago(self, payment_id: int) -> dict:
        response = self.sdk.payment().get(payment_id)
        if response["status"] != 200:
            raise RuntimeError(
                f"Error obteniendo pago de MP (status {response['status']}): {response['response']}"
            )
        return response["response"]


mp_client = MercadoPagoClient()
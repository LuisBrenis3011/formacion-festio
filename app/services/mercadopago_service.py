import mercadopago
from app.config import settings


class MercadoPagoError(Exception):
    """Excepción controlada para errores del SDK de Mercado Pago."""


class MercadoPagoClient:
    def __init__(self):
        self.sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)

    def generar_preferencia(
        self,
        pago_id: int,
        monto: float,
        titulo_evento: str,
        email_cliente: str,
        reserva_temp_id: str,
    ) -> str:
        frontend = settings.FRONTEND_URL.rstrip("/")

        preference_data = {
            "items": [
                {
                    "id": str(pago_id),
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
            "external_reference": str(pago_id),
            "metadata": {
                "reserva_temp_id": reserva_temp_id,
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
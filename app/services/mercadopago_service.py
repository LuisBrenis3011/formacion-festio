import mercadopago
from app.config import settings

class MercadoPagoClient:
    def __init__(self):
        # Inicializa con el token de tu archivo .env
        self.sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)

    def generar_preferencia(
        self, 
        pago_id: int, 
        monto: float, 
        titulo_evento: str, 
        email_cliente: str,
        reserva_temp_id: str
    ) -> str:
        """
        Crea la preferencia de pago y retorna la URL (init_point).
        """
        preference_data = {
            "items": [
                {
                    "title": f"Reserva en Festio: {titulo_evento}",
                    "quantity": 1,
                    "unit_price": float(monto),
                    "currency_id": "PEN"
                }
            ],
            "payer": {
                "email": email_cliente
            },
            "back_urls": {
                "success": "http://localhost:5173/pago-exitoso",
                "failure": "http://localhost:5173/pago-fallido",
                "pending": "http://localhost:5173/pago-pendiente"
            },
            "auto_return": "approved",
            # Vinculamos el ID de PagoTransaccion
            "external_reference": str(pago_id),
            # Guardamos el ID temporal de Redis para usarlo en el Webhook
            "metadata": {
                "reserva_temp_id": reserva_temp_id
            }
        }

        response = self.sdk.preference().create(preference_data)
        
        if response["status"] != 201:
            raise RuntimeError(f"Error en Mercado Pago: {response['response']}")
            
        # Para entorno local/pruebas usamos sandbox_init_point. 
        # En prod cambia a init_point.
        return response["response"]["sandbox_init_point"]

# Instancia global (Singleton) para usarla en todo el proyecto
mp_client = MercadoPagoClient()
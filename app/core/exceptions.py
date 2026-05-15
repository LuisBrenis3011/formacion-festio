from fastapi import HTTPException, status

class DisponibilidadException(HTTPException):
    def __init__(self, detail: str = "No hay disponibilidad para el horario solicitado"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)

class BloqueoExpiradoException(HTTPException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_408_REQUEST_TIMEOUT,
                         detail="El tiempo de bloqueo expiró. Por favor reinicia la reserva.")

class PagoFallidoException(HTTPException):
    def __init__(self, detail: str = "La transacción fue rechazada"):
        super().__init__(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail=detail)

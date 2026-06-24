from sqlalchemy.orm import Session
from app.repositories.base import BaseRepository
from app.domain.pagos.models import PagoTransaccion, Comprobante
from pydantic import BaseModel
from fastapi import Depends
from app.database import get_db

class PagoTransaccionRepository(BaseRepository[PagoTransaccion, BaseModel, BaseModel]):
    def __init__(self, db: Session):
        super().__init__(PagoTransaccion, db)

class ComprobanteRepository(BaseRepository[Comprobante, BaseModel, BaseModel]):
    def __init__(self, db: Session):
        super().__init__(Comprobante, db)

def get_pago_transaccion_repo(db: Session = Depends(get_db)) -> PagoTransaccionRepository: return PagoTransaccionRepository(db)
def get_comprobante_repo(db: Session = Depends(get_db)) -> ComprobanteRepository: return ComprobanteRepository(db)

from typing import List
from fastapi import HTTPException
from app.domain.reservas.models import Evento
from app.domain.reservas.schemas import EventoCreate
from app.repositories.reserva_repository import EventoRepository

def crear_evento(datos: EventoCreate, evento_repo: EventoRepository) -> Evento:
    evento = Evento(**datos.model_dump())
    evento_repo.db.add(evento)
    evento_repo.db.commit()
    evento_repo.db.refresh(evento)
    return evento

def obtener_evento(evento_id: int, evento_repo: EventoRepository) -> Evento:
    """Busca un evento por ID. Lanza 404 si no existe."""
    evento = evento_repo.get(evento_id)
    if not evento:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    return evento

def eventos_por_cliente(cliente_id: int, evento_repo: EventoRepository) -> List[Evento]:
    """Historial de eventos de un cliente."""
    return evento_repo.db.query(Evento).filter(Evento.cliente_id == cliente_id).all()

from typing import List

from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_proveedor
from app.domain.usuarios.models import Proveedor
from app.domain.reservas.schemas import ProveedorReservaItemOut
from app.services.reserva import reserva_gestion_service
from app.repositories.reserva_repository import get_reserva_repo, get_evento_repo
from app.repositories.usuario_repository import get_cliente_repo, get_usuario_repo
from app.repositories.catalogo_repository import get_paquete_repo, get_servicio_producto_repo

router = APIRouter()


@router.get("/mis-reservas", response_model=List[ProveedorReservaItemOut])
def mis_reservas_proveedor(
    proveedor: Proveedor = Depends(get_current_proveedor),
    reserva_repo = Depends(get_reserva_repo),
    evento_repo = Depends(get_evento_repo),
    cliente_repo = Depends(get_cliente_repo),
    usuario_repo = Depends(get_usuario_repo),
    paquete_repo = Depends(get_paquete_repo),
    servicio_repo = Depends(get_servicio_producto_repo),
):
    """Historial de reservas del proveedor autenticado (para su panel)."""
    return reserva_gestion_service.listar_reservas_proveedor(
        proveedor, reserva_repo, evento_repo, cliente_repo, usuario_repo, paquete_repo, servicio_repo
    )
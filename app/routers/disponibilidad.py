from fastapi import APIRouter, Depends
from app.core.dependencies import get_current_user
from app.domain.reservas.schemas import ConsultaDisponibilidadRequest, DisponibilidadResponse
from app.services import disponibilidad_service
from app.repositories.usuario_repository import ProveedorRepository, get_proveedor_repo
from app.repositories.catalogo_repository import ServicioProductoRepository, get_servicio_producto_repo
from app.repositories.disponibilidad_repository import (
    OcupacionServicioProductoRepository,
    OcupacionGlobalProveedorRepository,
    get_ocupacion_servicio_producto_repo,
    get_ocupacion_global_proveedor_repo
)
from app.services.bloqueo_service import tiempo_restante

router = APIRouter()


@router.post("/consultar", response_model=DisponibilidadResponse)
def consultar(
    datos: ConsultaDisponibilidadRequest,
    proveedor_repo: ProveedorRepository = Depends(get_proveedor_repo),
    servicio_repo: ServicioProductoRepository = Depends(get_servicio_producto_repo),
    ocupacion_sp_repo: OcupacionServicioProductoRepository = Depends(get_ocupacion_servicio_producto_repo),
    ocupacion_global_repo: OcupacionGlobalProveedorRepository = Depends(get_ocupacion_global_proveedor_repo),
    _: int = Depends(get_current_user)
):
    """
    Verifica si hay disponibilidad de stock para los ítems y 
    la capacidad del proveedor en las fechas/horas indicadas.
    """
    return disponibilidad_service.consultar_disponibilidad(
        proveedor_id=datos.proveedor_id,
        fecha_inicio=datos.fecha_evento_inicio,
        fecha_fin=datos.fecha_evento_fin,
        detalles=datos.detalles,
        proveedor_repo=proveedor_repo,
        servicio_repo=servicio_repo,
        ocupacion_sp_repo=ocupacion_sp_repo,
        ocupacion_global_repo=ocupacion_global_repo
    )


@router.get("/bloqueo/{reserva_temp_id}")
def estado_bloqueo(reserva_temp_id: str):
    """
    Retorna los segundos restantes del bloqueo temporal en Redis.
    El frontend lo usa para mostrar el contador de 10 minutos.
    """
    segundos = tiempo_restante(reserva_temp_id)
    return {
        "reserva_temp_id"  : reserva_temp_id,
        "segundos_restantes": segundos,
        "activo"           : segundos > 0,
    }
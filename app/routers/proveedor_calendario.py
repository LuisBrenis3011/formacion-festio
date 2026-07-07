from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field

from app.core.dependencies import get_current_proveedor
from app.domain.usuarios.models import Proveedor
from app.services import proveedor_calendario_service


class BloqueoCalendarioCreate(BaseModel):
    fecha: date
    motivo: Optional[str] = Field(None, max_length=300)


class BloqueoCalendarioOut(BaseModel):
    fecha: date
    motivo: Optional[str] = None
    created_at: str


router = APIRouter()


@router.get("/bloqueos", response_model=List[BloqueoCalendarioOut])
def listar_bloqueos(
    proveedor: Proveedor = Depends(get_current_proveedor),
):
    return proveedor_calendario_service.listar_bloqueos(proveedor.id)


@router.post("/bloqueos", response_model=BloqueoCalendarioOut, status_code=status.HTTP_201_CREATED)
def crear_bloqueo(
    datos: BloqueoCalendarioCreate,
    proveedor: Proveedor = Depends(get_current_proveedor),
):
    return proveedor_calendario_service.crear_bloqueo(
        proveedor.id,
        datos.fecha,
        datos.motivo,
    )


@router.delete("/bloqueos/{fecha}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_bloqueo(
    fecha: date,
    proveedor: Proveedor = Depends(get_current_proveedor),
):
    proveedor_calendario_service.eliminar_bloqueo(proveedor.id, fecha)

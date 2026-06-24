from typing import List, Dict, Any
from datetime import datetime
from fastapi import HTTPException
from app.domain.reservas.schemas import PreReservaCreate
from app.domain.catalogo.models import Paquete, ServicioProducto, DetallePaquete
from app.domain.common.enums import EstadoBasico
from app.repositories.catalogo_repository import PaqueteRepository, ServicioProductoRepository, DetallePaqueteRepository

def calcular_monto_total(detalles: List[Any], paquete_repo: PaqueteRepository, servicio_repo: ServicioProductoRepository) -> float:
    total = 0.0
    for d in detalles:
        if d.servicio_producto_id:
            servicio = servicio_repo.get(d.servicio_producto_id)
            if servicio:
                horas = d.horas_contratadas or servicio.duracion_base_horas or 1
                total += float(servicio.precio_unitario) * d.cantidad * horas
        elif d.paquete_id:
            paquete = paquete_repo.get(d.paquete_id)
            if paquete:
                total += float(paquete.precio_base)
    return round(total, 2)

def construir_carrito(
    datos: PreReservaCreate,
    paquete: Paquete,
    servicio_repo: ServicioProductoRepository,
    detalle_paquete_repo: DetallePaqueteRepository
):
    detalles_reserva = [{
        "paquete_id": paquete.id,
        "servicio_producto_id": None,
        "nombre": paquete.nombre,
        "tipo": "PAQUETE",
        "cantidad": 1,
        "horas_contratadas": None,
        "precio_unitario": float(paquete.precio_base or 0),
        "subtotal": float(paquete.precio_base or 0),
    }]
    items_ocupacion = []

    detalles_paquete = detalle_paquete_repo.db.query(DetallePaquete).filter(
        DetallePaquete.paquete_id == paquete.id
    ).all()
    for detalle in detalles_paquete:
        if not detalle.servicio_producto_id:
            continue
        items_ocupacion.append({
            "servicio_producto_id": detalle.servicio_producto_id,
            "cantidad": int(detalle.cantidad_incluida or 1),
        })

    total = float(paquete.precio_base or 0)
    for adicional in datos.adicionales:
        servicio = servicio_repo.db.query(ServicioProducto).filter(
            ServicioProducto.id == adicional.servicio_producto_id,
            ServicioProducto.proveedor_id == datos.proveedor_id,
            ServicioProducto.deleted_at == None,
        ).first()
        if not servicio or servicio.estado != EstadoBasico.ACTIVO:
            raise HTTPException(
                status_code=404,
                detail=f"Servicio adicional {adicional.servicio_producto_id} no disponible para el proveedor",
            )

        horas = adicional.horas_contratadas
        if horas is None and servicio.duracion_base_horas is not None:
            horas = float(servicio.duracion_base_horas)
        subtotal = subtotal_servicio(servicio, adicional.cantidad, horas)
        total += subtotal
        detalles_reserva.append({
            "paquete_id": None,
            "servicio_producto_id": servicio.id,
            "nombre": servicio.nombre,
            "tipo": "ADICIONAL",
            "cantidad": adicional.cantidad,
            "horas_contratadas": horas,
            "precio_unitario": float(servicio.precio_unitario or 0),
            "subtotal": subtotal,
        })
        items_ocupacion.append({
            "servicio_producto_id": servicio.id,
            "cantidad": adicional.cantidad,
        })

    return detalles_reserva, items_ocupacion, round(total, 2)

def subtotal_servicio(servicio: ServicioProducto, cantidad: int, horas: float | None) -> float:
    precio = float(servicio.precio_unitario or 0)
    if horas and (servicio.requiere_persona or "DJ" in (servicio.nombre or "").upper()):
        return round(precio * cantidad * horas, 2)
    return round(precio * cantidad, 2)

def agrupar_items(items: list[dict]) -> dict[int, int]:
    agrupados = {}
    for item in items:
        servicio_id = int(item["servicio_producto_id"])
        agrupados[servicio_id] = agrupados.get(servicio_id, 0) + int(item.get("cantidad") or 0)
    return agrupados

def personas_requeridas(items_ocupacion: list[dict], servicio_repo: ServicioProductoRepository) -> int:
    total = 0
    for servicio_id, cantidad in agrupar_items(items_ocupacion).items():
        servicio = servicio_repo.get(servicio_id)
        if servicio and servicio.requiere_persona:
            total += cantidad
    return total

def parse_datetime(valor) -> datetime:
    if isinstance(valor, datetime):
        return valor
    return datetime.fromisoformat(str(valor))

def se_solapan(inicio: datetime, fin: datetime, otro_inicio, otro_fin) -> bool:
    if not otro_inicio or not otro_fin:
        return False
    return parse_datetime(otro_inicio) < fin and parse_datetime(otro_fin) > inicio

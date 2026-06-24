"""
Lógica de negocio para los paquetes del proveedor autenticado.
Valida ownership de servicios al armar un paquete.
"""
from typing import List

from fastapi import HTTPException
from sqlalchemy.orm import joinedload

from app.domain.catalogo.models import (
    Categoria, DetallePaquete, Paquete, ServicioProducto, Tematica,
)
from app.domain.common.enums import EstadoBasico
from app.domain.usuarios.models import Proveedor
from app.domain.catalogo.schemas import ProveedorPaqueteCreate, ProveedorPaqueteUpdate

from app.repositories.catalogo_repository import (
    PaqueteRepository, DetallePaqueteRepository, CategoriaRepository,
    TematicaRepository, ServicioProductoRepository
)


def listar_paquetes(proveedor: Proveedor, repo: PaqueteRepository) -> List[Paquete]:
    """Lista paquetes del proveedor con detalles cargados."""
    return (
        repo.db.query(Paquete)
        .options(
            joinedload(Paquete.detalles).joinedload(DetallePaquete.servicio_producto),
        )
        .filter(
            Paquete.proveedor_id == proveedor.id,
            Paquete.estado == EstadoBasico.ACTIVO,
        )
        .order_by(Paquete.id.desc())
        .all()
    )


def obtener_paquete(paquete_id: int, proveedor: Proveedor, repo: PaqueteRepository) -> Paquete:
    """Busca un paquete que pertenezca al proveedor. Lanza 404 si no es suyo."""
    paquete = (
        repo.db.query(Paquete)
        .options(
            joinedload(Paquete.detalles).joinedload(DetallePaquete.servicio_producto),
        )
        .filter(
            Paquete.id == paquete_id,
            Paquete.proveedor_id == proveedor.id,
        )
        .first()
    )
    if not paquete:
        raise HTTPException(status_code=404, detail="Paquete no encontrado")
    return paquete


def crear_paquete(
    datos: ProveedorPaqueteCreate,
    proveedor: Proveedor,
    repo: PaqueteRepository,
    detalle_repo: DetallePaqueteRepository,
    categoria_repo: CategoriaRepository,
    tematica_repo: TematicaRepository,
    servicio_repo: ServicioProductoRepository,
) -> Paquete:
    """Crea un paquete con detalles. Valida ownership de cada servicio incluido."""
    # Validar categoría
    categoria = categoria_repo.get(datos.categoria_id)
    if not categoria:
        raise HTTPException(status_code=400, detail="Categoría no encontrada")

    # Validar temática (si se provee)
    if datos.tematica_id:
        tematica = tematica_repo.db.query(Tematica).filter(
            Tematica.id == datos.tematica_id,
            Tematica.categoria_id == datos.categoria_id,
        ).first()
        if not tematica:
            raise HTTPException(
                status_code=400,
                detail="Temática no encontrada o no pertenece a la categoría seleccionada",
            )

    # Validar que TODOS los servicios en detalles pertenezcan al proveedor
    if not datos.detalles:
        raise HTTPException(status_code=400, detail="El paquete debe incluir al menos un servicio")

    srv_ids = [d.servicio_producto_id for d in datos.detalles]
    servicios_propios = (
        servicio_repo.db.query(ServicioProducto.id)
        .filter(
            ServicioProducto.id.in_(srv_ids),
            ServicioProducto.proveedor_id == proveedor.id,
            ServicioProducto.deleted_at == None,
        )
        .all()
    )
    ids_validos = {s.id for s in servicios_propios}
    ids_invalidos = set(srv_ids) - ids_validos
    if ids_invalidos:
        raise HTTPException(
            status_code=400,
            detail=f"Los siguientes servicios no están en tu inventario: {ids_invalidos}",
        )

    paquete = Paquete(
        proveedor_id=proveedor.id,
        categoria_id=datos.categoria_id,
        tematica_id=datos.tematica_id,
        nombre=datos.nombre,
        descripcion=datos.descripcion,
        precio_base=datos.precio_base,
    )
    repo.db.add(paquete)
    repo.db.flush()

    for detalle in datos.detalles:
        detalle_repo.db.add(DetallePaquete(
            paquete_id=paquete.id,
            servicio_producto_id=detalle.servicio_producto_id,
            cantidad_incluida=detalle.cantidad_incluida,
        ))

    repo.db.commit()
    repo.db.refresh(paquete)
    # Re-cargar con joins
    return obtener_paquete(paquete.id, proveedor, repo)


def actualizar_paquete(
    paquete_id: int,
    datos: ProveedorPaqueteUpdate,
    proveedor: Proveedor,
    repo: PaqueteRepository,
    detalle_repo: DetallePaqueteRepository,
    servicio_repo: ServicioProductoRepository,
) -> Paquete:
    """Actualiza campos del paquete y opcionalmente reemplaza sus detalles."""
    paquete = obtener_paquete(paquete_id, proveedor, repo)

    # Actualizar campos simples
    campos_simples = datos.model_dump(exclude_unset=True, exclude={"detalles"})
    for campo, valor in campos_simples.items():
        setattr(paquete, campo, valor)

    # Si envían detalles, reemplazar la composición completa
    if datos.detalles is not None:
        if not datos.detalles:
            raise HTTPException(status_code=400, detail="El paquete debe incluir al menos un servicio")

        # Validar ownership de los nuevos servicios
        srv_ids = [d.servicio_producto_id for d in datos.detalles]
        servicios_propios = (
            servicio_repo.db.query(ServicioProducto.id)
            .filter(
                ServicioProducto.id.in_(srv_ids),
                ServicioProducto.proveedor_id == proveedor.id,
                ServicioProducto.deleted_at == None,
            )
            .all()
        )
        ids_validos = {s.id for s in servicios_propios}
        ids_invalidos = set(srv_ids) - ids_validos
        if ids_invalidos:
            raise HTTPException(
                status_code=400,
                detail=f"Servicios no válidos: {ids_invalidos}",
            )

        # Borrar detalles viejos y crear nuevos
        detalle_repo.db.query(DetallePaquete).filter(DetallePaquete.paquete_id == paquete.id).delete()
        for detalle in datos.detalles:
            detalle_repo.db.add(DetallePaquete(
                paquete_id=paquete.id,
                servicio_producto_id=detalle.servicio_producto_id,
                cantidad_incluida=detalle.cantidad_incluida,
            ))

    repo.db.commit()
    return obtener_paquete(paquete.id, proveedor, repo)


def eliminar_paquete(paquete_id: int, proveedor: Proveedor, repo: PaqueteRepository) -> None:
    """Soft delete: marca el paquete como INACTIVO."""
    paquete = obtener_paquete(paquete_id, proveedor, repo)
    paquete.estado = EstadoBasico.INACTIVO
    repo.db.commit()

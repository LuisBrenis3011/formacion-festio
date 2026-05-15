from typing import List

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.resena import Resena
from app.models.usuario import Proveedor
from app.schemas.pago import ResenaCreate


def listar_resenas_proveedor(proveedor_id: int, db: Session) -> List[Resena]:
    """Lista todas las reseñas de un proveedor."""
    return db.query(Resena).filter(Resena.proveedor_id == proveedor_id).all()


def crear_resena(datos: ResenaCreate, db: Session) -> Resena:
    """
    El cliente deja su reseña después de completar el evento.
    Valida la calificación y recalcula el promedio del proveedor.
    """
    if not (1 <= datos.calificacion <= 5):
        raise HTTPException(
            status_code=400, detail="La calificación debe ser entre 1 y 5"
        )

    resena = Resena(**datos.model_dump())
    db.add(resena)
    db.flush()

    # Recalcular el promedio del proveedor
    todas = db.query(Resena).filter(Resena.proveedor_id == datos.proveedor_id).all()
    promedio = sum(r.calificacion for r in todas) / len(todas)

    proveedor = db.query(Proveedor).filter(Proveedor.id == datos.proveedor_id).first()
    if proveedor:
        proveedor.calificacion_promedio = round(promedio, 2)

    db.commit()
    db.refresh(resena)
    return resena

from decimal import Decimal
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import app.domain.all_models  # noqa: F401
from app.core.security import hash_password
from app.database import SessionLocal
from app.domain.catalogo.models import Categoria, DetallePaquete, Paquete, ServicioProducto, Tematica
from app.domain.common.enums import EstadoBasico, EstadoVerificacion, RolUsuario
from app.domain.usuarios.models import Proveedor, Usuario


PASSWORD_DEMO = "demo123"


def main() -> None:
    db = SessionLocal()
    try:
        categorias = {
            "Show infantil": categoria(db, "Show infantil", "Shows para fiestas infantiles."),
            "Hora loca": categoria(db, "Hora loca", "Animación, baile y personajes para hora loca."),
            "Mobiliario": categoria(db, "Mobiliario", "Sillas, toldos y alquileres para eventos."),
            "Sonido y DJ": categoria(db, "Sonido y DJ", "Música, DJ y equipos de sonido."),
        }

        tematica(db, categorias["Show infantil"], "Spiderman")
        tematica(db, categorias["Show infantil"], "Frozen")
        tematica(db, categorias["Show infantil"], "Princesas")

        eym = proveedor(db, "EyM Eventos", "eym@festio.local", "Miraflores", 30)
        rayza = proveedor(db, "Rayza Kids", "rayza@festio.local", "Surco", 24)
        hz = proveedor(db, "HZ Producciones", "hz@festio.local", "San Miguel", 18)

        eym_servicios = [
            servicio(db, eym, categorias["Sonido y DJ"], "DJ animador EyM", "SERVICIO_HUMANO", True, 120, 3, 4),
            servicio(db, eym, categorias["Show infantil"], "Animadora infantil EyM", "SERVICIO_HUMANO", True, 90, 5, 4),
            servicio(db, eym, categorias["Hora loca"], "Bailarina hora loca EyM", "SERVICIO_HUMANO", True, 70, 20, 2),
            servicio(db, eym, categorias["Show infantil"], "Muñeco Spiderman EyM", "PRODUCTO_FISICO", False, 180, 2, None),
            servicio(db, eym, categorias["Show infantil"], "Muñeco Frozen EyM", "PRODUCTO_FISICO", False, 180, 1, None),
            servicio(db, eym, categorias["Mobiliario"], "Silla blanca plegable EyM", "PRODUCTO_FISICO", False, 3, 80, None),
            servicio(db, eym, categorias["Mobiliario"], "Toldo 4x4 EyM", "PRODUCTO_FISICO", False, 150, 4, None),
        ]
        paquete(
            db,
            eym,
            categorias["Show infantil"],
            "Show infantil base EyM",
            "Incluye animadora, DJ y dos bailarinas. Se puede ampliar con muñecos y mobiliario.",
            850,
            [(eym_servicios[0], 1), (eym_servicios[1], 1), (eym_servicios[2], 2)],
        )

        rayza_servicios = [
            servicio(db, rayza, categorias["Sonido y DJ"], "DJ Rayza", "SERVICIO_HUMANO", True, 100, 2, 4),
            servicio(db, rayza, categorias["Show infantil"], "Animadora Rayza", "SERVICIO_HUMANO", True, 85, 4, 4),
            servicio(db, rayza, categorias["Hora loca"], "Bailarina Rayza", "SERVICIO_HUMANO", True, 65, 12, 2),
            servicio(db, rayza, categorias["Show infantil"], "Muñeco Spiderman Rayza", "PRODUCTO_FISICO", False, 170, 1, None),
            servicio(db, rayza, categorias["Show infantil"], "Payaso infantil Rayza", "SERVICIO_HUMANO", True, 120, 2, 3),
        ]
        paquete(
            db,
            rayza,
            categorias["Show infantil"],
            "Show infantil económico Rayza",
            "Paquete infantil con animadora, DJ y bailarinas para eventos medianos.",
            720,
            [(rayza_servicios[0], 1), (rayza_servicios[1], 1), (rayza_servicios[2], 2)],
        )

        hz_servicios = [
            servicio(db, hz, categorias["Sonido y DJ"], "DJ premium HZ", "SERVICIO_HUMANO", True, 150, 2, 4),
            servicio(db, hz, categorias["Hora loca"], "Bailarín hora loca HZ", "SERVICIO_HUMANO", True, 75, 10, 2),
            servicio(db, hz, categorias["Mobiliario"], "Silla Tiffany HZ", "PRODUCTO_FISICO", False, 6, 120, None),
            servicio(db, hz, categorias["Mobiliario"], "Toldo elegante HZ", "PRODUCTO_FISICO", False, 220, 5, None),
            servicio(db, hz, categorias["Hora loca"], "Disfraz hora loca HZ", "PRODUCTO_FISICO", False, 55, 25, None),
        ]
        paquete(
            db,
            hz,
            categorias["Hora loca"],
            "Hora loca premium HZ",
            "Paquete de hora loca con DJ premium, bailarines y disfraces.",
            980,
            [(hz_servicios[0], 1), (hz_servicios[1], 4), (hz_servicios[4], 8)],
        )

        db.commit()
        print("Seed demo cargado correctamente.")
        print("Usuarios proveedores demo: eym@festio.local, rayza@festio.local, hz@festio.local")
        print(f"Password demo: {PASSWORD_DEMO}")
    finally:
        db.close()


def categoria(db, nombre: str, descripcion: str) -> Categoria:
    obj = db.query(Categoria).filter(Categoria.nombre == nombre).first()
    if not obj:
        obj = Categoria(nombre=nombre)
        db.add(obj)
        db.flush()
    obj.descripcion = descripcion
    return obj


def tematica(db, cat: Categoria, nombre: str) -> Tematica:
    obj = db.query(Tematica).filter(
        Tematica.categoria_id == cat.id,
        Tematica.nombre == nombre,
    ).first()
    if not obj:
        obj = Tematica(categoria_id=cat.id, nombre=nombre)
        db.add(obj)
        db.flush()
    return obj


def proveedor(db, nombre_empresa: str, email: str, distrito: str, capacidad: int) -> Proveedor:
    usuario = db.query(Usuario).filter(Usuario.email == email).first()
    if not usuario:
        usuario = Usuario(
            nombre=nombre_empresa,
            apellido="Demo",
            email=email,
            telefono="900000000",
            contrasena_hash=hash_password(PASSWORD_DEMO),
            rol=RolUsuario.PROVEEDOR,
            estado=EstadoBasico.ACTIVO,
        )
        db.add(usuario)
        db.flush()

    obj = db.query(Proveedor).filter(Proveedor.usuario_id == usuario.id).first()
    if not obj:
        obj = Proveedor(usuario_id=usuario.id)
        db.add(obj)
        db.flush()

    obj.nombre_empresa = nombre_empresa
    obj.ruc = f"20{usuario.id:09d}"
    obj.descripcion = f"Proveedor demo de Festio: {nombre_empresa}."
    obj.distrito = distrito
    obj.calificacion_promedio = Decimal("4.50")
    obj.estado_verificacion = EstadoVerificacion.VERIFICADO
    obj.capacidad_humana_total = capacidad
    return obj


def servicio(
    db,
    prov: Proveedor,
    cat: Categoria,
    nombre: str,
    tipo: str,
    requiere_persona: bool,
    precio: float,
    stock: int,
    horas: float | None,
) -> ServicioProducto:
    obj = db.query(ServicioProducto).filter(
        ServicioProducto.proveedor_id == prov.id,
        ServicioProducto.nombre == nombre,
    ).first()
    if not obj:
        obj = ServicioProducto(proveedor_id=prov.id, nombre=nombre)
        db.add(obj)
        db.flush()

    obj.categoria_id = cat.id
    obj.tipo = tipo
    obj.requiere_persona = requiere_persona
    obj.precio_unitario = Decimal(str(precio))
    obj.stock_maximo_simultaneo = stock
    obj.duracion_base_horas = Decimal(str(horas)) if horas is not None else None
    obj.estado = "ACTIVO"
    obj.deleted_at = None
    return obj


def paquete(
    db,
    prov: Proveedor,
    cat: Categoria,
    nombre: str,
    descripcion: str,
    precio: float,
    detalles: list[tuple[ServicioProducto, int]],
) -> Paquete:
    obj = db.query(Paquete).filter(
        Paquete.proveedor_id == prov.id,
        Paquete.nombre == nombre,
    ).first()
    if not obj:
        obj = Paquete(proveedor_id=prov.id, nombre=nombre)
        db.add(obj)
        db.flush()

    obj.categoria_id = cat.id
    obj.tematica_id = None
    obj.descripcion = descripcion
    obj.precio_base = Decimal(str(precio))
    obj.estado = EstadoBasico.ACTIVO

    for serv, cantidad in detalles:
        det = db.query(DetallePaquete).filter(
            DetallePaquete.paquete_id == obj.id,
            DetallePaquete.servicio_producto_id == serv.id,
        ).first()
        if not det:
            det = DetallePaquete(paquete_id=obj.id, servicio_producto_id=serv.id)
            db.add(det)
        det.cantidad_incluida = cantidad

    return obj


if __name__ == "__main__":
    main()

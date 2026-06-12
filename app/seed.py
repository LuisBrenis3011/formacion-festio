"""
Seed completo de Festio — Catálogo peruano enriquecido.

Fusiona las funciones constructoras seguras/idempotentes de scripts/seed_demo.py
con el catálogo peruano de 5 categorías macro y 30+ temáticas.

Ejecutar:
    python -m app.seed
"""
from decimal import Decimal
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.security import hash_password
from app.database import SessionLocal
from app.models.catalogo import Categoria, DetallePaquete, Paquete, ServicioProducto, Tematica
from app.models.enums import EstadoBasico, EstadoVerificacion, RolUsuario, TipoItemCatalogo
from app.models.usuario import Proveedor, Usuario


PASSWORD_DEMO = "festio2024"

def categoria(db, nombre: str, descripcion: str) -> Categoria:
    obj = db.query(Categoria).filter(Categoria.nombre == nombre).first()
    if not obj:
        obj = Categoria(nombre=nombre)
        db.add(obj)
    
    obj.descripcion = descripcion
    db.flush() # Se hace el flush con todos los datos llenos
    return obj


def tematica(db, cat: Categoria, nombre: str, imagen: str | None = None) -> Tematica:
    obj = db.query(Tematica).filter(
        Tematica.categoria_id == cat.id,
        Tematica.nombre == nombre,
    ).first()
    if not obj:
        obj = Tematica(categoria_id=cat.id, nombre=nombre)
        db.add(obj)
        
    if imagen:
        obj.imagen_referencial = imagen
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
        db.flush() # El usuario sí tiene todo listo desde el constructor

    obj = db.query(Proveedor).filter(Proveedor.usuario_id == usuario.id).first()
    if not obj:
        obj = Proveedor(usuario_id=usuario.id)
        db.add(obj)

    # Asignamos todo ANTES de enviarlo a la BD
    obj.nombre_empresa = nombre_empresa
    obj.ruc = f"20{usuario.id:09d}"
    obj.descripcion = f"Proveedor demo de Festio: {nombre_empresa}."
    obj.distrito = distrito
    obj.calificacion_promedio = Decimal("4.50")
    obj.estado_verificacion = EstadoVerificacion.VERIFICADO
    obj.capacidad_humana_total = capacidad
    db.flush() 
    return obj


def servicio(
    db,
    prov: Proveedor,
    cat: Categoria,
    nombre: str,
    tipo: TipoItemCatalogo,
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

    obj.categoria_id = cat.id
    obj.tipo = tipo
    obj.requiere_persona = requiere_persona
    obj.precio_unitario = Decimal(str(precio))
    obj.stock_maximo_simultaneo = stock
    obj.duracion_base_horas = Decimal(str(horas)) if horas is not None else None
    obj.estado = EstadoBasico.ACTIVO
    obj.deleted_at = None
    db.flush()
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
    """Crea o actualiza un paquete genérico (sin temática)."""
    obj = db.query(Paquete).filter(
        Paquete.proveedor_id == prov.id,
        Paquete.nombre == nombre,
    ).first()
    if not obj:
        obj = Paquete(proveedor_id=prov.id, nombre=nombre)
        db.add(obj)

    obj.categoria_id = cat.id
    obj.descripcion = descripcion
    obj.precio_base = Decimal(str(precio))
    obj.estado = EstadoBasico.ACTIVO
    db.flush()

    for serv, cantidad in detalles:
        det = db.query(DetallePaquete).filter(
            DetallePaquete.paquete_id == obj.id,
            DetallePaquete.servicio_producto_id == serv.id,
        ).first()
        if not det:
            det = DetallePaquete(paquete_id=obj.id, servicio_producto_id=serv.id)
            db.add(det)
        det.cantidad_incluida = cantidad
        db.flush()
        
    return obj


# Aliases cortos para los tipos de item
SERV = TipoItemCatalogo.SERVICIO
PROD = TipoItemCatalogo.PRODUCTO


# ═══════════════════════════════════════════════════════════════════════════════
# CATÁLOGO PERUANO — 5 CATEGORÍAS MACRO
# ═══════════════════════════════════════════════════════════════════════════════

CATEGORIAS_DATA = {
    "Shows Infantiles": "Shows temáticos para fiestas infantiles con personajes y animación.",
    "Hora Loca": "Animación, baile, zanqueros y personajes para hora loca.",
    "Mobiliario y Decoración": "Sillas, mesas, toldos, carpas y decoración para eventos.",
    "Personal y Música": "DJs, maestros de ceremonia, meseros y equipos de sonido.",
    "Locales y Espacios": "Salones, terrazas y locales campestres para todo tipo de evento.",
}

TEMATICAS_DATA = {
    "Shows Infantiles": [
        "Spiderman", "Granja de Zenón", "Bartolito", "Cars", "Princesas",
        "Superhéroes", "Mario Bros", "Luigi", "Mickey Mouse", "Minnie Mouse",
        "Pluto", "Goofy", "Sonic", "Plim Plim", "Blanca Nieves", "Frozen",
        "Elsa", "Merlina", "Barbie", "Minecraft", "Avengers", "Dinosaurios",
        "Unicornio", "Paw Patrol", "Peppa Pig", "Toy Story", "Moana", "Encanto",
    ],
    "Hora Loca": [
        "Selvática", "Folclórica/Huaylas", "Terror", "Policías", "Vaqueros",
        "Neón/Glow", "Carnaval", "Boda/Matrimonio", "Quinceañero",
    ],
    "Mobiliario y Decoración": [
        "Elegante/Bodas", "Vintage/Rústico", "Lounge", "Toldo Clásico",
        "Toldos y Carpas",
    ],
    "Personal y Música": [
        "Formal/Elegante", "Urbano/Crossover", "Animado", "Estándar",
        "Chicoteca/Adultos",
    ],
    "Locales y Espacios": [
        "Campestre", "Salón Cerrado", "Terraza", "Local Comercial",
    ],
}

# ── Distritos reales de Lima Norte / Lima Centro ──────────────────────────────
DISTRITOS_LIMA = [
    "San Martín de Porres", "Los Olivos", "Comas", "Independencia",
    "Carabayllo", "Puente Piedra", "Ancón", "Santa Rosa", "Rímac",
    "Cercado de Lima", "San Miguel", "Surco", "Miraflores", "Ate",
    "San Juan de Lurigancho", "Villa El Salvador", "Chorrillos",
    "La Molina", "Breña", "Jesús María",
]

# ── Empresas peruanas simuladas ──────────────────────────────────────────────
EMPRESAS = [
    ("EyM Eventos SAC", "eym@festio.local", "Miraflores", 30),
    ("Rayza Kids EIRL", "rayza@festio.local", "Surco", 24),
    ("HZ Producciones SRL", "hz@festio.local", "San Miguel", 18),
    ("Festikids Perú SAC", "festikids@festio.local", "Los Olivos", 25),
    ("Show Time Lima EIRL", "showtime@festio.local", "San Martín de Porres", 20),
    ("Magia & Sonrisas SAC", "magia@festio.local", "Comas", 22),
    ("Dulce Fiesta EIRL", "dulce@festio.local", "Independencia", 15),
    ("Full Party Perú SRL", "fullparty@festio.local", "Carabayllo", 28),
    ("Animaciones Arcoíris SAC", "arcoiris@festio.local", "Puente Piedra", 16),
    ("Super Show Lima EIRL", "supershow@festio.local", "Rímac", 20),
    ("Fiesta Total SAC", "fiestatotal@festio.local", "Cercado de Lima", 35),
    ("DJ Master Perú SRL", "djmaster@festio.local", "San Juan de Lurigancho", 12),
    ("Eventos Premium Lima SAC", "premium@festio.local", "La Molina", 30),
    ("Selva Loca Producciones EIRL", "selvaloca@festio.local", "Ate", 25),
    ("Toldo Express Lima SRL", "toldos@festio.local", "Chorrillos", 10),
    ("Fiestas del Norte SAC", "norte@festio.local", "Ancón", 18),
    ("Kermesse Kids EIRL", "kermesse@festio.local", "Santa Rosa", 14),
    ("Sonido Total Perú SAC", "sonido@festio.local", "Breña", 8),
    ("Locura Latina Show SRL", "locura@festio.local", "Jesús María", 22),
    ("Villa Fiesta SAC", "villa@festio.local", "Villa El Salvador", 20),
]


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    db = SessionLocal()
    try:
        # ── 1. Categorías ─────────────────────────────────────────────────────
        cats = {}
        for nombre, desc in CATEGORIAS_DATA.items():
            cats[nombre] = categoria(db, nombre, desc)
        print("✅ Categorías creadas/actualizadas")

        # ── 2. Temáticas ──────────────────────────────────────────────────────
        temas = {}  # {(cat_nombre, tema_nombre): Tematica}
        for cat_nombre, lista in TEMATICAS_DATA.items():
            for tema_nombre in lista:
                slug = tema_nombre.replace(" ", "_").lower()
                img = f"https://img.festio.pe/tematicas/{slug}.jpg"
                t = tematica(db, cats[cat_nombre], tema_nombre, imagen=img)
                temas[(cat_nombre, tema_nombre)] = t
        print(f"✅ {len(temas)} temáticas creadas/actualizadas")

        # ── 3. Proveedores ────────────────────────────────────────────────────
        provs = {}
        for nombre_emp, email, distrito, cap in EMPRESAS:
            provs[nombre_emp] = proveedor(db, nombre_emp, email, distrito, cap)
        print(f"✅ {len(provs)} proveedores creados/actualizados")

        # ── 4. Servicios/Productos por proveedor ─────────────────────────────
        # Organizamos servicios por empresa para poder armar paquetes con ellos.

        def _s(prov_obj, cat_nombre, nombre, tipo, req, precio, stock, horas=None):
            """Atajo para crear servicio vinculado a su categoría."""
            return servicio(db, prov_obj, cats[cat_nombre], nombre, tipo, req, precio, stock, horas)

        # ── EyM Eventos SAC ──
        p = provs["EyM Eventos SAC"]
        eym = [
            _s(p, "Personal y Música", "DJ animador EyM", SERV, True, 120, 3, 4),
            _s(p, "Shows Infantiles", "Animadora infantil EyM", SERV, True, 90, 5, 4),
            _s(p, "Hora Loca", "Bailarina hora loca EyM", SERV, True, 70, 20, 2),
            _s(p, "Shows Infantiles", "Muñeco Spiderman EyM", PROD, False, 180, 2),
            _s(p, "Shows Infantiles", "Muñeco Frozen EyM", PROD, False, 180, 1),
            _s(p, "Mobiliario y Decoración", "Silla blanca plegable EyM", PROD, False, 3, 80),
            _s(p, "Mobiliario y Decoración", "Toldo 4x4 EyM", PROD, False, 150, 4),
            _s(p, "Shows Infantiles", "Show de Princesas EyM", SERV, True, 400, 3, 2),
            _s(p, "Shows Infantiles", "Caritas Pintadas EyM", SERV, True, 150, 4, 2),
        ]

        # ── Rayza Kids EIRL ──
        p = provs["Rayza Kids EIRL"]
        rayza = [
            _s(p, "Personal y Música", "DJ Rayza", SERV, True, 100, 2, 4),
            _s(p, "Shows Infantiles", "Animadora Rayza", SERV, True, 85, 4, 4),
            _s(p, "Hora Loca", "Bailarina Rayza", SERV, True, 65, 12, 2),
            _s(p, "Shows Infantiles", "Muñeco Spiderman Rayza", PROD, False, 170, 1),
            _s(p, "Shows Infantiles", "Payaso infantil Rayza", SERV, True, 120, 2, 3),
            _s(p, "Shows Infantiles", "Show Granja de Zenón Rayza", SERV, True, 300, 3, 1.5),
            _s(p, "Shows Infantiles", "Show Mario Bros Rayza", SERV, True, 380, 3, 2),
        ]

        # ── HZ Producciones SRL ──
        p = provs["HZ Producciones SRL"]
        hz = [
            _s(p, "Personal y Música", "DJ premium HZ", SERV, True, 150, 2, 4),
            _s(p, "Hora Loca", "Bailarín hora loca HZ", SERV, True, 75, 10, 2),
            _s(p, "Mobiliario y Decoración", "Silla Tiffany HZ", PROD, False, 6, 120),
            _s(p, "Mobiliario y Decoración", "Toldo elegante HZ", PROD, False, 220, 5),
            _s(p, "Hora Loca", "Disfraz hora loca HZ", PROD, False, 55, 25),
            _s(p, "Hora Loca", "Zanquero HZ", SERV, True, 250, 4, 1),
        ]

        # ── Festikids Perú SAC ──
        p = provs["Festikids Perú SAC"]
        festikids = [
            _s(p, "Shows Infantiles", "Show Spiderman Festikids", SERV, True, 350, 3, 2),
            _s(p, "Shows Infantiles", "Show Paw Patrol Festikids", SERV, True, 320, 3, 2),
            _s(p, "Shows Infantiles", "Show Peppa Pig Festikids", SERV, True, 280, 3, 1.5),
            _s(p, "Shows Infantiles", "Animadora Festikids", SERV, True, 200, 5, 2),
            _s(p, "Shows Infantiles", "Show de Burbujas Festikids", SERV, True, 120, 2, 1),
            _s(p, "Shows Infantiles", "Piñata personalizada Festikids", PROD, False, 120, 5),
        ]

        # ── Show Time Lima EIRL ──
        p = provs["Show Time Lima EIRL"]
        showtime = [
            _s(p, "Shows Infantiles", "Show Avengers ShowTime", SERV, True, 400, 4, 2),
            _s(p, "Shows Infantiles", "Show Minecraft ShowTime", SERV, True, 350, 3, 2),
            _s(p, "Shows Infantiles", "Show Sonic ShowTime", SERV, True, 330, 3, 2),
            _s(p, "Shows Infantiles", "Animadora ShowTime", SERV, True, 200, 5, 2),
            _s(p, "Shows Infantiles", "Muñeco extra ShowTime", PROD, False, 100, 10),
        ]

        # ── Magia & Sonrisas SAC ──
        p = provs["Magia & Sonrisas SAC"]
        magia = [
            _s(p, "Shows Infantiles", "Show Encanto Magia", SERV, True, 380, 3, 2),
            _s(p, "Shows Infantiles", "Show Moana Magia", SERV, True, 370, 3, 2),
            _s(p, "Shows Infantiles", "Show Toy Story Magia", SERV, True, 360, 3, 2),
            _s(p, "Shows Infantiles", "Animadora Magia", SERV, True, 190, 5, 2),
            _s(p, "Shows Infantiles", "Caritas pintadas Magia", SERV, True, 150, 4, 2),
        ]

        # ── Dulce Fiesta EIRL ──
        p = provs["Dulce Fiesta EIRL"]
        dulce = [
            _s(p, "Shows Infantiles", "Show Unicornio Dulce", SERV, True, 320, 3, 2),
            _s(p, "Shows Infantiles", "Show Barbie Dulce", SERV, True, 340, 3, 2),
            _s(p, "Shows Infantiles", "Animadora Dulce Fiesta", SERV, True, 180, 4, 2),
            _s(p, "Shows Infantiles", "Show Merlina Dulce", SERV, True, 350, 3, 2),
        ]

        # ── Full Party Perú SRL ──
        p = provs["Full Party Perú SRL"]
        fullparty = [
            _s(p, "Hora Loca", "Hora Loca Selvática Full Party", SERV, True, 500, 6, 1),
            _s(p, "Hora Loca", "Hora Loca Folclórica Full Party", SERV, True, 450, 6, 1),
            _s(p, "Hora Loca", "Bailarín extra Full Party", SERV, True, 150, 10, 1),
            _s(p, "Hora Loca", "Máquina de humo Full Party", PROD, False, 180, 4),
            _s(p, "Hora Loca", "Luces LED Full Party", PROD, False, 220, 10),
        ]

        # ── Animaciones Arcoíris SAC ──
        p = provs["Animaciones Arcoíris SAC"]
        arcoiris = [
            _s(p, "Hora Loca", "Hora Loca Terror Arcoíris", SERV, True, 480, 6, 1),
            _s(p, "Hora Loca", "Hora Loca Policías Arcoíris", SERV, True, 460, 6, 1),
            _s(p, "Hora Loca", "Zanquero Arcoíris", SERV, True, 250, 4, 1),
            _s(p, "Hora Loca", "Arlequín Arcoíris", SERV, True, 200, 4, 1),
        ]

        # ── Super Show Lima EIRL ──
        p = provs["Super Show Lima EIRL"]
        supershow = [
            _s(p, "Hora Loca", "Hora Loca Vaqueros SuperShow", SERV, True, 470, 6, 1),
            _s(p, "Hora Loca", "Hora Loca Neón SuperShow", SERV, True, 520, 6, 1),
            _s(p, "Hora Loca", "Bailarina Neón SuperShow", SERV, True, 160, 8, 1),
            _s(p, "Hora Loca", "Kit Neón/Glow SuperShow", PROD, False, 200, 15),
        ]

        # ── Fiesta Total SAC ──
        p = provs["Fiesta Total SAC"]
        fiestatotal = [
            _s(p, "Hora Loca", "Hora Loca Carnaval Fiesta Total", SERV, True, 550, 8, 1),
            _s(p, "Hora Loca", "Hora Loca Boda Fiesta Total", SERV, True, 600, 8, 1),
            _s(p, "Hora Loca", "Hora Loca Quinceañero Fiesta Total", SERV, True, 580, 8, 1),
            _s(p, "Personal y Música", "DJ Fiesta Total", SERV, True, 500, 2, 5),
            _s(p, "Personal y Música", "Maestro de ceremonia Fiesta Total", SERV, True, 350, 1, 4),
            _s(p, "Personal y Música", "Mesero uniformado Fiesta Total", SERV, True, 150, 10, 8),
        ]

        # ── DJ Master Perú SRL ──
        p = provs["DJ Master Perú SRL"]
        djmaster = [
            _s(p, "Personal y Música", "DJ Urbano DJMaster", SERV, True, 600, 1, 5),
            _s(p, "Personal y Música", "DJ Chicoteca DJMaster", SERV, True, 500, 1, 4),
            _s(p, "Personal y Música", "Sonido profesional DJMaster", PROD, False, 500, 3),
        ]

        # ── Eventos Premium Lima SAC ──
        p = provs["Eventos Premium Lima SAC"]
        premium = [
            _s(p, "Personal y Música", "DJ Formal Premium", SERV, True, 700, 1, 5),
            _s(p, "Personal y Música", "Maestro de ceremonia Premium", SERV, True, 400, 1, 4),
            _s(p, "Personal y Música", "Mesero Premium", SERV, True, 180, 12, 8),
            _s(p, "Mobiliario y Decoración", "Decoración completa Premium", SERV, True, 750, 4, 4),
        ]

        # ── Selva Loca Producciones EIRL ──
        p = provs["Selva Loca Producciones EIRL"]
        selvaloca = [
            _s(p, "Hora Loca", "Hora Loca Selvática Selva Loca", SERV, True, 550, 8, 1),
            _s(p, "Hora Loca", "Bailarín selvático Selva Loca", SERV, True, 160, 12, 1),
            _s(p, "Hora Loca", "Kit cotillón selvático Selva Loca", PROD, False, 250, 20),
        ]

        # ── Toldo Express Lima SRL ──
        p = provs["Toldo Express Lima SRL"]
        toldos = [
            _s(p, "Mobiliario y Decoración", "Alquiler mesas Toldo Express", PROD, False, 25, 50),
            _s(p, "Mobiliario y Decoración", "Sillas Tiffany Toldo Express", PROD, False, 18, 100),
            _s(p, "Mobiliario y Decoración", "Sillas plásticas Toldo Express", PROD, False, 5, 200),
            _s(p, "Mobiliario y Decoración", "Toldo clásico 6x6 Toldo Express", PROD, False, 300, 10),
        ]

        # ── Fiestas del Norte SAC ──
        p = provs["Fiestas del Norte SAC"]
        norte = [
            _s(p, "Shows Infantiles", "Show Dinosaurios Norte", SERV, True, 360, 3, 2),
            _s(p, "Shows Infantiles", "Show Cars Norte", SERV, True, 340, 3, 2),
            _s(p, "Shows Infantiles", "Animadora Norte", SERV, True, 180, 5, 2),
        ]

        # ── Kermesse Kids EIRL ──
        p = provs["Kermesse Kids EIRL"]
        kermesse = [
            _s(p, "Shows Infantiles", "Show Mickey Mouse Kermesse", SERV, True, 300, 3, 2),
            _s(p, "Shows Infantiles", "Show Plim Plim Kermesse", SERV, True, 280, 3, 1.5),
            _s(p, "Shows Infantiles", "Animadora Kermesse Kids", SERV, True, 170, 4, 2),
        ]

        # ── Sonido Total Perú SAC ──
        p = provs["Sonido Total Perú SAC"]
        sonido = [
            _s(p, "Personal y Música", "DJ Animado Sonido Total", SERV, True, 450, 2, 5),
            _s(p, "Personal y Música", "Sonido profesional Sonido Total", PROD, False, 480, 3),
        ]

        # ── Locura Latina Show SRL ──
        p = provs["Locura Latina Show SRL"]
        locura = [
            _s(p, "Hora Loca", "Hora Loca Folclórica Locura Latina", SERV, True, 500, 6, 1),
            _s(p, "Hora Loca", "Zanquero Locura Latina", SERV, True, 260, 4, 1),
            _s(p, "Hora Loca", "Bailarín Huaylas Locura Latina", SERV, True, 180, 8, 1),
        ]

        # ── Villa Fiesta SAC ──
        p = provs["Villa Fiesta SAC"]
        villa = [
            _s(p, "Locales y Espacios", "Salón campestre Villa Fiesta", PROD, False, 2000, 1),
            _s(p, "Locales y Espacios", "Terraza con vista Villa Fiesta", PROD, False, 1800, 1),
            _s(p, "Locales y Espacios", "Salón cerrado climatizado Villa Fiesta", PROD, False, 2500, 1),
            _s(p, "Mobiliario y Decoración", "Decoración elegante Villa Fiesta", SERV, True, 800, 3, 4),
        ]

        print("✅ Servicios/productos creados/actualizados")

        # ── 5. Paquetes (30+) distribuidos por distritos y temáticas ─────────

        # ── Shows Infantiles ──
        paquete(db, provs["EyM Eventos SAC"], cats["Shows Infantiles"],
                "Show Infantil Spiderman EyM",
                "Show completo de Spiderman con animadora, DJ y bailarinas.",
                850, [(eym[0], 1), (eym[1], 1), (eym[2], 2), (eym[3], 1)])

        paquete(db, provs["EyM Eventos SAC"], cats["Shows Infantiles"],
                "Show Frozen Mágico EyM",
                "Princesa Elsa, animadora y show de burbujas para la fiesta perfecta.",
                920, [(eym[1], 1), (eym[4], 1), (eym[8], 1)])

        paquete(db, provs["EyM Eventos SAC"], cats["Shows Infantiles"],
                "Combo Princesas Real EyM",
                "Show de princesas con caritas pintadas y decoración.",
                1200, [(eym[7], 1), (eym[1], 1), (eym[8], 1), (eym[2], 2)])

        paquete(db, provs["Rayza Kids EIRL"], cats["Shows Infantiles"],
                "Show Infantil Económico Rayza",
                "Paquete infantil con animadora, DJ y bailarinas para eventos medianos.",
                720, [(rayza[0], 1), (rayza[1], 1), (rayza[2], 2)])

        paquete(db, provs["Rayza Kids EIRL"], cats["Shows Infantiles"],
                "Combo Granja de Zenón Rayza",
                "Show completo de la Granja de Zenón con Bartolito y animación.",
                880, [(rayza[5], 1), (rayza[1], 1), (rayza[0], 1)])

        paquete(db, provs["Rayza Kids EIRL"], cats["Shows Infantiles"],
                "Combo Mario Bros Rayza",
                "Mario y Luigi en tu fiesta con show completo y animación.",
                950, [(rayza[6], 1), (rayza[1], 1), (rayza[4], 1)])

        paquete(db, provs["Festikids Perú SAC"], cats["Shows Infantiles"],
                "Combo Spiderman Festikids",
                "Show de Spiderman con animadora, burbujas y piñata temática.",
                900, [(festikids[0], 1), (festikids[3], 1), (festikids[4], 1), (festikids[5], 1)])

        paquete(db, provs["Festikids Perú SAC"], cats["Shows Infantiles"],
                "Combo Paw Patrol Festikids",
                "Los cachorros de Paw Patrol en tu fiesta con animación completa.",
                850, [(festikids[1], 1), (festikids[3], 1), (festikids[4], 1)])

        paquete(db, provs["Festikids Perú SAC"], cats["Shows Infantiles"],
                "Combo Peppa Pig Festikids",
                "Peppa Pig y sus amigos animan tu fiesta infantil.",
                780, [(festikids[2], 1), (festikids[3], 1), (festikids[4], 1)])

        paquete(db, provs["Show Time Lima EIRL"], cats["Shows Infantiles"],
                "Combo Avengers ShowTime",
                "Los Avengers al completo: Iron Man, Capitán América y más.",
                1100, [(showtime[0], 1), (showtime[3], 1), (showtime[4], 2)])

        paquete(db, provs["Show Time Lima EIRL"], cats["Shows Infantiles"],
                "Combo Minecraft ShowTime",
                "Steve y Creeper en vivo para los gamers más pequeños.",
                950, [(showtime[1], 1), (showtime[3], 1), (showtime[4], 1)])

        paquete(db, provs["Show Time Lima EIRL"], cats["Shows Infantiles"],
                "Combo Sonic ShowTime",
                "Sonic y sus amigos con velocidad y diversión.",
                900, [(showtime[2], 1), (showtime[3], 1)])

        paquete(db, provs["Magia & Sonrisas SAC"], cats["Shows Infantiles"],
                "Combo Encanto Magia",
                "La familia Madrigal en tu fiesta con show de Mirabel y Bruno.",
                980, [(magia[0], 1), (magia[3], 1), (magia[4], 1)])

        paquete(db, provs["Magia & Sonrisas SAC"], cats["Shows Infantiles"],
                "Combo Moana Magia",
                "Aventura polinesia con Moana y Maui.",
                960, [(magia[1], 1), (magia[3], 1), (magia[4], 1)])

        paquete(db, provs["Dulce Fiesta EIRL"], cats["Shows Infantiles"],
                "Combo Unicornio Dulce",
                "Fiesta mágica de unicornios con arcoíris y animación.",
                820, [(dulce[0], 1), (dulce[2], 1)])

        paquete(db, provs["Dulce Fiesta EIRL"], cats["Shows Infantiles"],
                "Combo Barbie Dulce",
                "El mundo rosa de Barbie con show y decoración.",
                860, [(dulce[1], 1), (dulce[2], 1)])

        paquete(db, provs["Dulce Fiesta EIRL"], cats["Shows Infantiles"],
                "Combo Merlina Dulce",
                "La misteriosa Merlina en tu fiesta con ambientación dark.",
                900, [(dulce[3], 1), (dulce[2], 1)])

        paquete(db, provs["Fiestas del Norte SAC"], cats["Shows Infantiles"],
                "Combo Dinosaurios Norte",
                "T-Rex y sus amigos jurásicos en tu fiesta.",
                880, [(norte[0], 1), (norte[2], 1)])

        paquete(db, provs["Fiestas del Norte SAC"], cats["Shows Infantiles"],
                "Combo Cars Norte",
                "Rayo McQueen y Mate en la pista de tu fiesta.",
                840, [(norte[1], 1), (norte[2], 1)])

        paquete(db, provs["Kermesse Kids EIRL"], cats["Shows Infantiles"],
                "Combo Mickey Mouse Kermesse",
                "Mickey y Minnie para la fiesta clásica Disney.",
                800, [(kermesse[0], 1), (kermesse[2], 1)])

        paquete(db, provs["Kermesse Kids EIRL"], cats["Shows Infantiles"],
                "Combo Plim Plim Kermesse",
                "El payaso más querido anima tu fiesta infantil.",
                750, [(kermesse[1], 1), (kermesse[2], 1)])

        # ── Hora Loca ──
        paquete(db, provs["HZ Producciones SRL"], cats["Hora Loca"],
                "Hora Loca Premium HZ",
                "Paquete de hora loca con DJ premium, bailarines y disfraces.",
                980, [(hz[0], 1), (hz[1], 4), (hz[4], 8)])

        paquete(db, provs["Full Party Perú SRL"], cats["Hora Loca"],
                "Hora Loca Selvática Full Party",
                "Hora loca selvática con bailarines, máquina de humo y luces LED.",
                1100, [(fullparty[0], 1), (fullparty[2], 4), (fullparty[3], 1), (fullparty[4], 2)])

        paquete(db, provs["Full Party Perú SRL"], cats["Hora Loca"],
                "Hora Loca Folclórica Full Party",
                "Huaylas, tunantada y cotillón peruano para la hora loca.",
                1000, [(fullparty[1], 1), (fullparty[2], 4), (fullparty[4], 2)])

        paquete(db, provs["Animaciones Arcoíris SAC"], cats["Hora Loca"],
                "Hora Loca Terror Arcoíris",
                "Zombies, momias y terror divertido para la hora loca.",
                950, [(arcoiris[0], 1), (arcoiris[2], 2), (arcoiris[3], 2)])

        paquete(db, provs["Animaciones Arcoíris SAC"], cats["Hora Loca"],
                "Hora Loca Policías Arcoíris",
                "Policías y ladrones en la hora loca más divertida.",
                940, [(arcoiris[1], 1), (arcoiris[2], 2)])

        paquete(db, provs["Super Show Lima EIRL"], cats["Hora Loca"],
                "Hora Loca Neón SuperShow",
                "Fiesta neón con DJ, luces UV, bailarines y kit glow.",
                1350, [(supershow[1], 1), (supershow[2], 4), (supershow[3], 10)])

        paquete(db, provs["Super Show Lima EIRL"], cats["Hora Loca"],
                "Hora Loca Vaqueros SuperShow",
                "Vaqueros, lassos y rodeo para una hora loca country.",
                980, [(supershow[0], 1), (supershow[2], 3)])

        paquete(db, provs["Fiesta Total SAC"], cats["Hora Loca"],
                "Hora Loca Carnaval Fiesta Total",
                "Carnaval brasileño con plumas, lentejuelas y mucha alegría.",
                1200, [(fiestatotal[0], 1), (fiestatotal[3], 1)])

        paquete(db, provs["Fiesta Total SAC"], cats["Hora Loca"],
                "Hora Loca Boda Fiesta Total",
                "Hora loca elegante para matrimonios con DJ y bailarines.",
                1400, [(fiestatotal[1], 1), (fiestatotal[3], 1), (fiestatotal[4], 1)])

        paquete(db, provs["Fiesta Total SAC"], cats["Hora Loca"],
                "Hora Loca Quinceañero Fiesta Total",
                "Quinceañero de ensueño con hora loca temática.",
                1300, [(fiestatotal[2], 1), (fiestatotal[3], 1)])

        paquete(db, provs["Selva Loca Producciones EIRL"], cats["Hora Loca"],
                "Selva Extrema Selva Loca",
                "Selvática extrema con máquina de humo y cotillón premium.",
                1100, [(selvaloca[0], 1), (selvaloca[1], 6), (selvaloca[2], 10)])

        paquete(db, provs["Locura Latina Show SRL"], cats["Hora Loca"],
                "Hora Loca Huaylas Locura Latina",
                "Danza Huaylas auténtica con zanqueros y bailarines.",
                1050, [(locura[0], 1), (locura[1], 2), (locura[2], 4)])

        # ── Mobiliario y Decoración ──
        paquete(db, provs["Toldo Express Lima SRL"], cats["Mobiliario y Decoración"],
                "Paquete Mobiliario Elegante Toldo Express",
                "Sillas Tiffany, mesas y toldo 6x6 para bodas y eventos elegantes.",
                2000, [(toldos[0], 10), (toldos[1], 50), (toldos[3], 1)])

        paquete(db, provs["Toldo Express Lima SRL"], cats["Mobiliario y Decoración"],
                "Paquete Económico Toldo Express",
                "Sillas plásticas, mesas y toldo clásico para fiestas familiares.",
                800, [(toldos[0], 8), (toldos[2], 60), (toldos[3], 1)])

        paquete(db, provs["Eventos Premium Lima SAC"], cats["Mobiliario y Decoración"],
                "Decoración Boda de Ensueño Premium",
                "Decoración completa de bodas: mesas, centros de mesa, cortinaje premium.",
                3500, [(premium[3], 1)])

        # ── Personal y Música ──
        paquete(db, provs["DJ Master Perú SRL"], cats["Personal y Música"],
                "DJ Urbano Full DJMaster",
                "DJ urbano/crossover con sonido profesional y luces para toda la noche.",
                1800, [(djmaster[0], 1), (djmaster[2], 1)])

        paquete(db, provs["DJ Master Perú SRL"], cats["Personal y Música"],
                "DJ Chicoteca DJMaster",
                "DJ para chicoteca y fiesta de adultos con repertorio variado.",
                1500, [(djmaster[1], 1), (djmaster[2], 1)])

        paquete(db, provs["Eventos Premium Lima SAC"], cats["Personal y Música"],
                "Ceremonia de Lujo Premium",
                "Maestro de ceremonia, meseros y DJ formal para evento de gala.",
                2200, [(premium[0], 1), (premium[1], 1), (premium[2], 4)])

        paquete(db, provs["Sonido Total Perú SAC"], cats["Personal y Música"],
                "Pack DJ Animado Sonido Total",
                "DJ animado con sonido profesional para fiestas familiares.",
                1400, [(sonido[0], 1), (sonido[1], 1)])

        paquete(db, provs["Fiesta Total SAC"], cats["Personal y Música"],
                "Pack Servicio Estándar Fiesta Total",
                "DJ + maestro de ceremonia + meseros para evento mediano.",
                1600, [(fiestatotal[3], 1), (fiestatotal[4], 1), (fiestatotal[5], 4)])

        # ── Locales y Espacios ──
        paquete(db, provs["Villa Fiesta SAC"], cats["Locales y Espacios"],
                "Campestre Full Day Villa Fiesta",
                "Local campestre por 12 horas con estacionamiento y juegos infantiles.",
                3200, [(villa[0], 1), (villa[3], 1)])

        paquete(db, provs["Villa Fiesta SAC"], cats["Locales y Espacios"],
                "Terraza VIP Villa Fiesta",
                "Terraza con vista panorámica y decoración elegante.",
                2800, [(villa[1], 1), (villa[3], 1)])

        paquete(db, provs["Villa Fiesta SAC"], cats["Locales y Espacios"],
                "Salón Climatizado Villa Fiesta",
                "Salón cerrado con aire acondicionado y decoración incluida.",
                3000, [(villa[2], 1), (villa[3], 1)])

        db.commit()
        print("─" * 60)
        print("🎉 Seed completo cargado correctamente.")
        print(f"   Password demo: {PASSWORD_DEMO}")
        print("   Emails proveedores:")
        for _, email, _, _ in EMPRESAS:
            print(f"      • {email}")
        print("─" * 60)

    except Exception as e:
        db.rollback()
        print(f"❌ Error durante el seed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
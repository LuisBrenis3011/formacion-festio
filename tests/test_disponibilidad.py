"""
tests/test_disponibilidad.py

TASK-TEST-04 — Tests de disponibilidad (integración vía TestClient).

Cubre:
- app/routers/disponibilidad.py  (POST /consultar)
- app/services/disponibilidad_service.py (consultar_disponibilidad)

BUG CONFIRMADO (con evidencia, ver test_bloqueo_temporal_cuenta_como_ocupacion):
`disponibilidad_service.consultar_disponibilidad()` NUNCA lee Redis. Solo
suma desde las tablas OcupacionServicioProducto / OcupacionGlobalProveedor
en BD. Peor aún: `bloqueo_service.listar_bloqueos()` ya existe y su propio
docstring dice "para considerar pre-reservas en disponibilidad" — es una
función construida exactamente para este propósito, pero nunca se integró
en disponibilidad_service.py. Es código huérfano, no solo un gap de diseño.

Impacto real: mientras un cliente tiene un prebloqueo activo (10 minutos)
sobre la última unidad de stock de un ítem, un segundo cliente consultando
disponibilidad en paralelo ve ese ítem como disponible y puede iniciar su
propio prebloqueo sobre el mismo cupo. El conflicto solo se resuelve más
tarde, en el checkout (cuando efectivamente falte stock real en BD), no en
el paso de consulta donde el usuario esperaría enterarse.

Se documenta con `xfail(strict=True)`, mismo criterio usado en
TASK-BIZ-05: no se toca disponibilidad_service.py en esta rama de testing;
el fix (llamar a listar_bloqueos() y sumar sus cantidades al SUM existente
antes de comparar contra el stock) le corresponde a
refactor/pagos-y-notificaciones o a una tarea nueva tipo TASK-BIZ-08.
"""

from datetime import datetime, timedelta, timezone

import pytest

from app.domain.catalogo.models import Categoria, ServicioProducto
from app.domain.disponibilidad.models import (
    OcupacionServicioProducto,
    OcupacionGlobalProveedor,
)
from app.domain.common.enums import TipoItemCatalogo, EstadoBasico
from app.services import bloqueo_service


ENDPOINT = "/api/disponibilidad/consultar"


# ---------------------------------------------------------------------------
# Helpers de setup
# ---------------------------------------------------------------------------
def _rango_evento():
    """Rango de fechas válido (futuro) reutilizado por los tests."""
    inicio = datetime.now(timezone.utc) + timedelta(days=1)
    fin = inicio + timedelta(hours=5)
    return inicio, fin


def _crear_categoria(db_session):
    categoria = Categoria(nombre="Shows Infantiles", descripcion="Categoria de prueba")
    db_session.add(categoria)
    db_session.commit()
    db_session.refresh(categoria)
    return categoria


def _crear_servicio_producto(
    db_session,
    proveedor_id,
    categoria_id,
    stock_maximo_simultaneo,
    requiere_persona=False,
    estado=EstadoBasico.ACTIVO,
):
    servicio = ServicioProducto(
        proveedor_id=proveedor_id,
        categoria_id=categoria_id,
        nombre="Animador Infantil",
        tipo=TipoItemCatalogo.SERVICIO,  # <- ajustar si el enum tiene otro nombre
        requiere_persona=requiere_persona,
        precio_unitario=150.00,
        stock_maximo_simultaneo=stock_maximo_simultaneo,
        estado=estado,
    )
    db_session.add(servicio)
    db_session.commit()
    db_session.refresh(servicio)
    return servicio


def _payload_consulta(proveedor_id, inicio, fin, detalles):
    return {
        "proveedor_id": proveedor_id,
        "fecha_evento_inicio": inicio.isoformat(),
        "fecha_evento_fin": fin.isoformat(),
        "detalles": detalles,
    }


# ---------------------------------------------------------------------------
# 1. Caso feliz: todo disponible
# ---------------------------------------------------------------------------
def test_consultar_disponibilidad_todo_disponible(
    client, db_session, usuario_proveedor, auth_headers_cliente
):
    categoria = _crear_categoria(db_session)
    proveedor = usuario_proveedor.proveedor

    servicio = _crear_servicio_producto(
        db_session,
        proveedor_id=proveedor.id,
        categoria_id=categoria.id,
        stock_maximo_simultaneo=5,
    )

    inicio, fin = _rango_evento()
    payload = _payload_consulta(
        proveedor.id,
        inicio,
        fin,
        [{"servicio_producto_id": servicio.id, "cantidad": 2}],
    )

    response = client.post(ENDPOINT, json=payload, headers=auth_headers_cliente)

    assert response.status_code == 200
    data = response.json()
    assert data["disponible"] is True
    assert data["items_no_disponibles"] is None


# ---------------------------------------------------------------------------
# 2. Stock agotado por ocupaciones solapadas (SUM agregado)
# ---------------------------------------------------------------------------
def test_consultar_stock_agotado_retorna_no_disponible(
    client, db_session, usuario_proveedor, auth_headers_cliente
):
    categoria = _crear_categoria(db_session)
    proveedor = usuario_proveedor.proveedor

    servicio = _crear_servicio_producto(
        db_session,
        proveedor_id=proveedor.id,
        categoria_id=categoria.id,
        stock_maximo_simultaneo=2,
    )

    inicio, fin = _rango_evento()

    # Ocupación existente que solapa completamente el rango consultado y
    # consume todo el stock disponible (2/2).
    ocupacion = OcupacionServicioProducto(
        servicio_producto_id=servicio.id,
        fecha_hora_inicio=inicio,
        fecha_hora_fin=fin,
        cantidad_ocupada=2,
    )
    db_session.add(ocupacion)
    db_session.commit()

    payload = _payload_consulta(
        proveedor.id,
        inicio,
        fin,
        [{"servicio_producto_id": servicio.id, "cantidad": 1}],
    )

    response = client.post(ENDPOINT, json=payload, headers=auth_headers_cliente)

    assert response.status_code == 200
    data = response.json()
    assert data["disponible"] is False
    assert data["items_no_disponibles"] is not None
    assert any("Animador Infantil" in item for item in data["items_no_disponibles"])


# ---------------------------------------------------------------------------
# 3. Capacidad humana total del proveedor excedida
# ---------------------------------------------------------------------------
def test_consultar_capacidad_humana_excedida(
    client, db_session, usuario_proveedor, auth_headers_cliente
):
    categoria = _crear_categoria(db_session)
    proveedor = usuario_proveedor.proveedor

    # Tope físico bajo a propósito: 5 personas.
    proveedor.capacidad_humana_total = 5
    db_session.add(proveedor)
    db_session.commit()

    # Stock del ítem holgado (no es el cuello de botella en este test).
    servicio = _crear_servicio_producto(
        db_session,
        proveedor_id=proveedor.id,
        categoria_id=categoria.id,
        stock_maximo_simultaneo=10,
        requiere_persona=True,
    )

    inicio, fin = _rango_evento()

    # Ya hay 4 personas ocupadas en el mismo rango horario -> cupo libre = 1.
    ocupacion_global = OcupacionGlobalProveedor(
        proveedor_id=proveedor.id,
        fecha_hora_inicio=inicio,
        fecha_hora_fin=fin,
        total_personas_ocupadas=4,
    )
    db_session.add(ocupacion_global)
    db_session.commit()

    # Se piden 2 personas más -> 2 > cupo_libre (1) -> no disponible.
    payload = _payload_consulta(
        proveedor.id,
        inicio,
        fin,
        [{"servicio_producto_id": servicio.id, "cantidad": 2}],
    )

    response = client.post(ENDPOINT, json=payload, headers=auth_headers_cliente)

    assert response.status_code == 200
    data = response.json()
    assert data["disponible"] is False
    assert data["items_no_disponibles"] is not None
    assert any(
        "Capacidad humana del proveedor" in item for item in data["items_no_disponibles"]
    )


# ---------------------------------------------------------------------------
# 4. Proveedor inexistente
# ---------------------------------------------------------------------------
def test_consultar_proveedor_inexistente(client, auth_headers_cliente):
    inicio, fin = _rango_evento()

    payload = _payload_consulta(999999, inicio, fin, [])

    response = client.post(ENDPOINT, json=payload, headers=auth_headers_cliente)

    # ⚠️ Nota de consistencia (no es un bug que se corrija en esta rama):
    # a diferencia de /api/reservas/prebloquear, que devuelve 404 cuando el
    # proveedor no existe, este servicio siempre responde 200 con
    # disponible=False. Documentamos el comportamiento actual tal como está;
    # si se decide unificar el criterio, sería un ítem aparte para
    # refactor/pagos-y-notificaciones o una rama de consistencia de API.
    assert response.status_code == 200
    data = response.json()
    assert data["disponible"] is False
    assert data["mensaje"] == "Proveedor no encontrado"


# ---------------------------------------------------------------------------
# 5. Bloqueo temporal (Redis) como ocupación — BUG CONFIRMADO
# ---------------------------------------------------------------------------
@pytest.mark.xfail(
    strict=True,
    reason=(
        "TASK-BIZ-08 (sugerido): consultar_disponibilidad() no consulta "
        "bloqueo_service.listar_bloqueos(), que existe justamente para "
        "esto segun su propio docstring ('considerar pre-reservas en "
        "disponibilidad'). Un prebloqueo activo de 10 minutos sobre la "
        "unica unidad de stock no se descuenta, y un segundo cliente "
        "consultando disponibilidad en paralelo ve el item como "
        "disponible cuando en realidad ya esta comprometido."
    ),
)
def test_bloqueo_temporal_cuenta_como_ocupacion(
    client, db_session, usuario_proveedor, auth_headers_cliente
):
    categoria = _crear_categoria(db_session)
    proveedor = usuario_proveedor.proveedor

    # Stock de una sola unidad: cualquier bloqueo activo deberia agotarlo.
    servicio = _crear_servicio_producto(
        db_session,
        proveedor_id=proveedor.id,
        categoria_id=categoria.id,
        stock_maximo_simultaneo=1,
    )

    inicio, fin = _rango_evento()

    # Simula el prebloqueo de 10 minutos que crearia
    # POST /api/reservas/prebloquear al reservar la unica unidad
    # disponible. El contenido exacto del dict no importa: bloqueo_service
    # solo lo serializa con json.dumps, y disponibilidad_service ni
    # siquiera lo lee.
    bloqueo_service.crear_bloqueo(
        "temp-test-bloqueo-001",
        {
            "servicio_producto_id": servicio.id,
            "cantidad": 1,
            "fecha_hora_inicio": inicio.isoformat(),
            "fecha_hora_fin": fin.isoformat(),
        },
    )

    payload = _payload_consulta(
        proveedor.id,
        inicio,
        fin,
        [{"servicio_producto_id": servicio.id, "cantidad": 1}],
    )

    response = client.post(ENDPOINT, json=payload, headers=auth_headers_cliente)

    assert response.status_code == 200
    data = response.json()
    # Comportamiento ESPERADO: la unica unidad ya esta temporalmente
    # bloqueada por otro cliente en el mismo rango horario, asi que no
    # deberia aparecer como disponible. HOY esto falla (da True) porque
    # el servicio ignora los bloqueos activos en Redis.
    assert data["disponible"] is False
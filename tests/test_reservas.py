"""
tests/test_reservas.py

TASK-TEST-02 — Tests de reservas y checkout.

Estado: 11 de 11 tests del backlog implementados.
"""
from datetime import datetime, timedelta, timezone

from app.domain.catalogo.models import Categoria, Paquete
from app.domain.common.enums import EstadoBasico, EstadoReserva
from app.domain.reservas.models import Evento, Reserva
from app.domain.usuarios.models import Cliente, Proveedor

RESERVAS_PREFIX = "/api/reservas"


def _fecha_futura(dias=7, horas=0):
    return (datetime.now(timezone.utc) + timedelta(days=dias, hours=horas)).isoformat()


def _payload_prebloqueo(**overrides):
    payload = {
        "proveedor_id": 1,
        "paquete_id": 1,
        "nombre_evento": "Fiesta de cumpleaños",
        "tipo_evento": "Cumpleaños",
        "fecha_evento_inicio": _fecha_futura(dias=7),
        "fecha_evento_fin": _fecha_futura(dias=7, horas=4),
        "direccion": "Av. Test 123, Miraflores",
        "aforo_estimado": 50,
        "adicionales": [],
    }
    payload.update(overrides)
    return payload


def _crear_paquete(db_session, proveedor_id, estado=EstadoBasico.ACTIVO, precio_base=100.00):
    categoria = Categoria(nombre="Cumpleaños", descripcion="Categoria de prueba")
    db_session.add(categoria)
    db_session.commit()
    db_session.refresh(categoria)

    paquete = Paquete(
        proveedor_id=proveedor_id,
        categoria_id=categoria.id,
        nombre="Paquete Test",
        precio_base=precio_base,
        estado=estado,
    )
    db_session.add(paquete)
    db_session.commit()
    db_session.refresh(paquete)
    return paquete


def _prebloquear(client, proveedor_id, paquete_id):
    """Helper: ejecuta un prebloqueo exitoso y retorna el JSON de respuesta."""
    response = client.post(
        f"{RESERVAS_PREFIX}/prebloquear",
        json=_payload_prebloqueo(proveedor_id=proveedor_id, paquete_id=paquete_id),
    )
    assert response.status_code == 200, response.text
    return response.json()


# ---------------------------------------------------------------------------
# Validaciones puras de Pydantic (no requieren proveedor/paquete reales)
# ---------------------------------------------------------------------------

def test_prebloquear_fecha_pasada_retorna_422(client):
    ayer = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    response = client.post(
        f"{RESERVAS_PREFIX}/prebloquear",
        json=_payload_prebloqueo(
            fecha_evento_inicio=ayer,
            fecha_evento_fin=_fecha_futura(dias=1),
        ),
    )

    assert response.status_code == 422


def test_prebloquear_fin_antes_inicio_retorna_422(client):
    inicio = _fecha_futura(dias=7)
    fin_antes = _fecha_futura(dias=6)  # anterior al inicio
    response = client.post(
        f"{RESERVAS_PREFIX}/prebloquear",
        json=_payload_prebloqueo(
            fecha_evento_inicio=inicio,
            fecha_evento_fin=fin_antes,
        ),
    )

    assert response.status_code == 422


def test_cantidad_cero_retorna_422(client):
    response = client.post(
        f"{RESERVAS_PREFIX}/prebloquear",
        json=_payload_prebloqueo(
            adicionales=[{"servicio_producto_id": 1, "cantidad": 0}]
        ),
    )

    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Prebloqueo: casos de error que ocurren ANTES de tocar Redis
# ---------------------------------------------------------------------------

def test_prebloquear_proveedor_inexistente_retorna_404(client):
    response = client.post(
        f"{RESERVAS_PREFIX}/prebloquear",
        json=_payload_prebloqueo(proveedor_id=999999, paquete_id=999999),
    )

    assert response.status_code == 404


def test_prebloquear_paquete_inactivo_retorna_404(client, db_session, usuario_proveedor):
    proveedor = db_session.query(Proveedor).filter(
        Proveedor.usuario_id == usuario_proveedor.id
    ).first()
    paquete_inactivo = _crear_paquete(db_session, proveedor.id, estado=EstadoBasico.INACTIVO)

    response = client.post(
        f"{RESERVAS_PREFIX}/prebloquear",
        json=_payload_prebloqueo(proveedor_id=proveedor.id, paquete_id=paquete_inactivo.id),
    )

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Prebloqueo exitoso
# ---------------------------------------------------------------------------

def test_prebloquear_exitoso_retorna_temp_id(client, db_session, usuario_proveedor):
    proveedor = db_session.query(Proveedor).filter(
        Proveedor.usuario_id == usuario_proveedor.id
    ).first()
    paquete = _crear_paquete(db_session, proveedor.id, precio_base=100.00)

    data = _prebloquear(client, proveedor.id, paquete.id)

    assert "reserva_temp_id" in data and data["reserva_temp_id"]
    assert data["proveedor_id"] == proveedor.id
    assert data["paquete_id"] == paquete.id
    assert data["monto_total"] == 100.00
    assert data["monto_adelanto"] == 10.00
    assert data["monto_pendiente"] == 90.00
    assert data["minutos_restantes"] == 10
    assert len(data["detalles"]) == 1


# ---------------------------------------------------------------------------
# Checkout: bloqueo expirado (no requiere prebloqueo previo exitoso)
# ---------------------------------------------------------------------------

def test_checkout_simulado_bloqueo_expirado_retorna_408(client):
    response = client.post(
        f"{RESERVAS_PREFIX}/checkout-simulado/id-inexistente-o-expirado",
        json={"metodo_pago": "TARJETA"},
    )

    assert response.status_code == 408


# ---------------------------------------------------------------------------
# Checkout simulado exitoso (flujo completo: prebloqueo -> checkout)
# ---------------------------------------------------------------------------

def test_checkout_simulado_exitoso(
    client, db_session, usuario_proveedor, usuario_cliente, auth_headers_cliente
):
    proveedor = db_session.query(Proveedor).filter(
        Proveedor.usuario_id == usuario_proveedor.id
    ).first()
    paquete = _crear_paquete(db_session, proveedor.id, precio_base=100.00)

    prebloqueo = _prebloquear(client, proveedor.id, paquete.id)
    temp_id = prebloqueo["reserva_temp_id"]

    response = client.post(
        f"{RESERVAS_PREFIX}/checkout-simulado/{temp_id}",
        json={"metodo_pago": "TARJETA"},
        headers=auth_headers_cliente,
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["estado_pago"] == "APROBADO"
    assert data["monto_total"] == 100.00
    assert data["monto_adelanto"] == 10.00
    assert data["monto_pendiente"] == 90.00
    assert "reserva_id" in data
    assert "pago_id" in data

    # El bloqueo debe haberse liberado tras confirmar el checkout
    reintento = client.post(
        f"{RESERVAS_PREFIX}/checkout-simulado/{temp_id}",
        json={"metodo_pago": "TARJETA"},
        headers=auth_headers_cliente,
    )
    assert reintento.status_code == 408


def test_checkout_sin_datos_cliente_retorna_400(client, db_session, usuario_proveedor):
    proveedor = db_session.query(Proveedor).filter(
        Proveedor.usuario_id == usuario_proveedor.id
    ).first()
    paquete = _crear_paquete(db_session, proveedor.id, precio_base=100.00)

    prebloqueo = _prebloquear(client, proveedor.id, paquete.id)
    temp_id = prebloqueo["reserva_temp_id"]

    # Sin header de autenticación y sin nombre/email/password en el body
    response = client.post(
        f"{RESERVAS_PREFIX}/checkout-simulado/{temp_id}",
        json={"metodo_pago": "TARJETA"},
    )

    assert response.status_code == 400


# ---------------------------------------------------------------------------
# Cancelación y listado (usan reserva_gestion_service, no tocan Redis)
# ---------------------------------------------------------------------------

def test_cancelar_reserva_completada_retorna_400(
    client, db_session, usuario_cliente, usuario_proveedor, auth_headers_cliente
):
    cliente = db_session.query(Cliente).filter(Cliente.usuario_id == usuario_cliente.id).first()
    proveedor = db_session.query(Proveedor).filter(Proveedor.usuario_id == usuario_proveedor.id).first()

    evento = Evento(
        cliente_id=cliente.id,
        nombre_evento="Evento Test",
        fecha_evento_inicio=datetime.now(timezone.utc) + timedelta(days=7),
        fecha_evento_fin=datetime.now(timezone.utc) + timedelta(days=7, hours=4),
        direccion="Av. Test 123",
    )
    db_session.add(evento)
    db_session.commit()
    db_session.refresh(evento)

    reserva = Reserva(
        evento_id=evento.id,
        proveedor_id=proveedor.id,
        estado=EstadoReserva.COMPLETADA,
        monto_total=100.00,
        monto_adelanto=10.00,
        monto_pendiente=90.00,
    )
    db_session.add(reserva)
    db_session.commit()
    db_session.refresh(reserva)

    response = client.patch(
        f"{RESERVAS_PREFIX}/{reserva.id}/cancelar",
        headers=auth_headers_cliente,
    )

    assert response.status_code == 400


def test_mis_reservas_retorna_lista(
    client, db_session, usuario_cliente, usuario_proveedor, auth_headers_cliente
):
    cliente = db_session.query(Cliente).filter(Cliente.usuario_id == usuario_cliente.id).first()
    proveedor = db_session.query(Proveedor).filter(Proveedor.usuario_id == usuario_proveedor.id).first()

    evento = Evento(
        cliente_id=cliente.id,
        nombre_evento="Evento Confirmado",
        fecha_evento_inicio=datetime.now(timezone.utc) + timedelta(days=10),
        fecha_evento_fin=datetime.now(timezone.utc) + timedelta(days=10, hours=3),
        direccion="Av. Test 456",
    )
    db_session.add(evento)
    db_session.commit()
    db_session.refresh(evento)

    reserva = Reserva(
        evento_id=evento.id,
        proveedor_id=proveedor.id,
        estado=EstadoReserva.CONFIRMADA,
        monto_total=200.00,
        monto_adelanto=20.00,
        monto_pendiente=180.00,
    )
    db_session.add(reserva)
    db_session.commit()
    db_session.refresh(reserva)

    response = client.get(f"{RESERVAS_PREFIX}/mis-reservas", headers=auth_headers_cliente)

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["reserva_id"] == reserva.id
    assert data[0]["nombre_empresa"] == proveedor.nombre_empresa
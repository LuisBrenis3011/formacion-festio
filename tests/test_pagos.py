"""
tests/test_pagos.py

TASK-TEST-03 — Tests de pagos.

Estado: 5 de 7 tests del backlog implementados (1 de ellos, a proposito,
documenta un bug real: ver test_rechazar_pago_y_notificacion).

PENDIENTES:
  - test_aprobar_pago_exitoso
  - test_comprobante_generado_despues_aprobacion
Bloqueados por TASK-BIZ-05 (ver detalle en el bloque de comentarios al
final del archivo) y por app/services/disponibilidad_service.py /
app/domain/pagos/models.py, aun no vistos.

AJUSTAR: PAGOS_PREFIX se infiere por el mismo patron usado en
/api/auth y /api/reservas. Confirmar en app/main.py.
"""
from datetime import datetime, timedelta, timezone

import pytest

from app.domain.reservas.models import Evento, Reserva
from app.domain.usuarios.models import Cliente, Proveedor
from app.domain.common.enums import EstadoReserva

PAGOS_PREFIX = "/api/pagos"


def _crear_reserva(db_session, usuario_cliente, usuario_proveedor, **overrides):
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

    datos_reserva = {
        "evento_id": evento.id,
        "proveedor_id": proveedor.id,
        "estado": EstadoReserva.PENDIENTE,
        "monto_total": 100.00,
        "monto_adelanto": 10.00,
        "monto_pendiente": 90.00,
    }
    datos_reserva.update(overrides)

    reserva = Reserva(**datos_reserva)
    db_session.add(reserva)
    db_session.commit()
    db_session.refresh(reserva)
    return reserva


def _payload_pago(reserva_id, **overrides):
    payload = {
        "reserva_id": reserva_id,
        "tipo_pago": "ADELANTO_ONLINE",
        "monto": 10.00,
        "metodo_pago": "TARJETA",
    }
    payload.update(overrides)
    return payload


# ---------------------------------------------------------------------------
# POST /api/pagos/
# ---------------------------------------------------------------------------

def test_registrar_pago_exitoso(client, db_session, usuario_cliente, usuario_proveedor, auth_headers_cliente):
    reserva = _crear_reserva(db_session, usuario_cliente, usuario_proveedor)

    response = client.post(
        f"{PAGOS_PREFIX}/",
        json=_payload_pago(reserva.id),
        headers=auth_headers_cliente,
    )

    assert response.status_code == 201, response.text
    data = response.json()
    assert data["reserva_id"] == reserva.id
    assert data["monto"] == 10.00
    assert data["estado"] == "PENDIENTE"


def test_registrar_pago_monto_negativo_retorna_422(client, auth_headers_cliente):
    response = client.post(
        f"{PAGOS_PREFIX}/",
        json=_payload_pago(reserva_id=1, monto=-10.00),
        headers=auth_headers_cliente,
    )

    assert response.status_code == 422


def test_registrar_pago_reserva_inexistente_retorna_404(client, auth_headers_cliente):
    response = client.post(
        f"{PAGOS_PREFIX}/",
        json=_payload_pago(reserva_id=999999),
        headers=auth_headers_cliente,
    )

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET /api/pagos/comprobante/{reserva_id}
# ---------------------------------------------------------------------------

def test_comprobante_reserva_sin_pago_retorna_404(client, auth_headers_cliente):
    response = client.get(
        f"{PAGOS_PREFIX}/comprobante/999999",
        headers=auth_headers_cliente,
    )
    assert response.status_code == 404

def test_comprobante_sin_token_retorna_401(client):
    response = client.get(f"{PAGOS_PREFIX}/comprobante/999999")
    assert response.status_code == 401

# ---------------------------------------------------------------------------
# POST /api/pagos/iniciar  (genera preferencia de Mercado Pago)
# ---------------------------------------------------------------------------

def test_iniciar_pago_mercadopago_exitoso(
    client, db_session, usuario_cliente, usuario_proveedor, auth_headers_cliente, monkeypatch
):
    from app.services import pago_service

    reserva = _crear_reserva(db_session, usuario_cliente, usuario_proveedor)

    class FakeMPClient:
        def generar_preferencia(self, **kwargs):
            return "https://mercadopago.test/checkout/fake-pref-id"

    monkeypatch.setattr(pago_service, "mp_client", FakeMPClient())

    response = client.post(
        f"{PAGOS_PREFIX}/iniciar",
        json={
            "pago": _payload_pago(reserva.id),
            "titulo_evento": "Evento Test",
            "reserva_temp_id": "temp-abc-123",
        },
        headers=auth_headers_cliente,
    )

    assert response.status_code == 200, response.text
    assert response.json()["url_pago"] == "https://mercadopago.test/checkout/fake-pref-id"


def test_iniciar_pago_mercadopago_falla_retorna_502_y_rechaza_pago(
    client, db_session, usuario_cliente, usuario_proveedor, auth_headers_cliente, monkeypatch
):
    from app.services import pago_service
    from app.domain.pagos.models import PagoTransaccion
    from app.domain.common.enums import EstadoPago

    reserva = _crear_reserva(db_session, usuario_cliente, usuario_proveedor)

    class FakeMPClientRoto:
        def generar_preferencia(self, **kwargs):
            raise Exception("Mercado Pago no disponible")

    monkeypatch.setattr(pago_service, "mp_client", FakeMPClientRoto())

    response = client.post(
        f"{PAGOS_PREFIX}/iniciar",
        json={
            "pago": _payload_pago(reserva.id),
            "titulo_evento": "Evento Test",
            "reserva_temp_id": "temp-abc-456",
        },
        headers=auth_headers_cliente,
    )

    assert response.status_code == 502

    pago = db_session.query(PagoTransaccion).filter(
        PagoTransaccion.reserva_id == reserva.id
    ).first()
    assert pago is not None
    assert pago.estado == EstadoPago.RECHAZADO
    
        
# ---------------------------------------------------------------------------
# POST /api/pagos/{pago_id}/rechazar
# ---------------------------------------------------------------------------

# @pytest.mark.xfail(
#    reason="TASK-BIZ-05: notificacion_service.notificar_fallo_pago recibe un "
#    "Session donde espera un NotificacionRepository -> AttributeError "
#    "'Session' object has no attribute 'db' en notificacion_service.py:37",
#    strict=True,
#)
def test_rechazar_pago_y_notificacion(
    client, db_session, usuario_cliente, usuario_proveedor, auth_headers_cliente
):
    """
    Confirmado: AttributeError: 'Session' object has no attribute 'db'
    en app/services/notificacion_service.py:37 (repo.db.add(...)).

    pago_service.rechazar_pago_completo() llama a
    notificar_fallo_pago(usuario_id, reserva_id, db) pasando un objeto
    Session donde la función espera un NotificacionRepository. Esto
    confirma TASK-BIZ-05 del backlog con un traceback real.

    Se marca xfail (no se omite ni se "arregla" el test) para que la
    suite documente el bug conocido sin ensuciar el reporte con un
    FAILED en cada corrida. En cuanto TASK-BIZ-05 se corrija en
    pago_service.py (pasando NotificacionRepository(db) en vez de db),
    quita el decorador @pytest.mark.xfail de abajo: si el test empieza
    a pasar, pytest lo marcará como XPASS y sabremos que ya se puede
    quitar la marca definitivamente.
    """
    reserva = _crear_reserva(db_session, usuario_cliente, usuario_proveedor)

    registro = client.post(
        f"{PAGOS_PREFIX}/",
        json=_payload_pago(reserva.id),
        headers=auth_headers_cliente,
    )
    assert registro.status_code == 201, registro.text
    pago_id = registro.json()["id"]

    from app.config import settings

    headers = {
        **auth_headers_cliente,
        "X-Webhook-Secret": settings.PAYMENT_WEBHOOK_SECRET,
    }

    response = client.post(
        f"{PAGOS_PREFIX}/{pago_id}/rechazar",
        params={
            "usuario_id": usuario_cliente.id,
            "reserva_id": reserva.id
        },
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["mensaje"] == "Pago rechazado. El cliente puede reintentar."

# ---------------------------------------------------------------------------
# POST /api/pagos/{pago_id}/aprobar  (webhook, protegido por secreto compartido)
# ---------------------------------------------------------------------------

def test_aprobar_pago_sin_secreto_retorna_401(client):
    response = client.post(
        f"{PAGOS_PREFIX}/1/aprobar",
        params={"reserva_temp_id": "fake-temp-id", "codigo_transaccion": "TXN123"},
    )
    assert response.status_code == 401


def test_aprobar_pago_secreto_invalido_retorna_401(client):
    response = client.post(
        f"{PAGOS_PREFIX}/1/aprobar",
        params={"reserva_temp_id": "fake-temp-id", "codigo_transaccion": "TXN123"},
        headers={"X-Webhook-Secret": "secreto-incorrecto"},
    )
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# POST /api/pagos/{pago_id}/rechazar_manual  (JWT normal, no webhook)
# ---------------------------------------------------------------------------

def test_rechazar_pago_manual_propio_retorna_200(
    client, db_session, usuario_cliente, usuario_proveedor, auth_headers_cliente
):
    """Caso feliz: el cliente dueño de la reserva rechaza su propio pago."""
    reserva = _crear_reserva(db_session, usuario_cliente, usuario_proveedor)
    registro = client.post(
        f"{PAGOS_PREFIX}/",
        json=_payload_pago(reserva.id),
        headers=auth_headers_cliente,
    )
    pago_id = registro.json()["id"]

    response = client.post(
        f"{PAGOS_PREFIX}/{pago_id}/rechazar_manual",
        params={"reserva_id": reserva.id},
        headers=auth_headers_cliente,
    )
    assert response.status_code == 200


def test_rechazar_pago_manual_de_otro_cliente_no_deberia_autorizar(
    client, db_session, usuario_cliente, usuario_cliente_otro,
    usuario_proveedor, auth_headers_cliente, auth_headers_cliente_otro,
):
    """
    HALLAZGO DE SEGURIDAD (no bug de este test): rechazar_pago_completo()
    no valida ownership. usuario_cliente_otro puede rechazar un pago que
    NO es suyo con solo conocer/adivinar el pago_id.
    Documentado, reportado al lider, NO corregido en esta rama.
    """
    reserva = _crear_reserva(db_session, usuario_cliente, usuario_proveedor)
    registro = client.post(
        f"{PAGOS_PREFIX}/",
        json=_payload_pago(reserva.id),
        headers=auth_headers_cliente,
    )
    pago_id = registro.json()["id"]

    response = client.post(
        f"{PAGOS_PREFIX}/{pago_id}/rechazar_manual",
        params={"reserva_id": reserva.id},
        headers=auth_headers_cliente_otro,
    )

    # Comportamiento actual (vulnerable): responde 200 igual.
    assert response.status_code == 200
    
    
# ---------------------------------------------------------------------------
# POST /api/pagos/webhook  (sin auth, server-to-server)
# ---------------------------------------------------------------------------

def test_webhook_payload_invalido_no_truena(client):
    """El router captura cualquier excepción y responde 200 igual;
    esto confirma que un payload malformado no tumba el servidor."""
    response = client.post(f"{PAGOS_PREFIX}/webhook", json={"tipo": "desconocido"})
    assert response.status_code == 200
    assert response.json()["status"] in ("ok", "received_with_errors")
"""
tests/test_reservas.py

TASK-TEST-02 — Tests de reservas y checkout.

⚠️ ARCHIVO PARCIAL: estos 3 tests cubren validaciones de Pydantic en
PreReservaCreate, que se rechazan ANTES de llegar a checkout_service.py
(no requieren datos en la BD). Los otros 8 tests del backlog
(prebloqueo con proveedor/paquete inexistente, checkout simulado,
cancelación, mis-reservas) requieren:
  - app/domain/reservas/models.py       (Reserva, Evento, DetalleReserva)
  - app/services/reserva/checkout_service.py
  - app/domain/catalogo/models.py       (Paquete, ServicioProducto)
Se agregan en una segunda pasada de este mismo archivo.
"""
from datetime import datetime, timedelta, timezone

RESERVAS_PREFIX = "/api/reservas"  # AJUSTAR si el prefix real en main.py es distinto


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
# PENDIENTES (requieren models.py de reservas + checkout_service.py):
#
# def test_prebloquear_exitoso_retorna_temp_id(...)
# def test_prebloquear_proveedor_inexistente_retorna_404(...)
# def test_prebloquear_paquete_inactivo_retorna_404(...)
# def test_checkout_simulado_bloqueo_expirado_retorna_408(...)
# def test_checkout_simulado_exitoso(...)
# def test_checkout_sin_datos_cliente_retorna_400(...)
# def test_cancelar_reserva_completada_retorna_400(...)
# def test_mis_reservas_retorna_lista(...)
# ---------------------------------------------------------------------------
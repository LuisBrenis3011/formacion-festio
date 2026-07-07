from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from app.domain.usuarios.schemas import (
    UsuarioCreate,
    RegistroProveedorRequest,
)
from app.domain.reservas.schemas import (
    EventoCreate,
    DetalleReservaCreate,
)
from app.domain.pagos.schemas import (
    PagoCreate,
    ResenaCreate,
)
from app.domain.catalogo.schemas import (
    ServicioProductoCreate,
)

from app.domain.common.enums import (
    RolUsuario,
    TipoPago,
    MetodoPago,
    TipoItemCatalogo,
)


# ============================================================
# TASK-TEST-05
# Tests unitarios puros de Pydantic
# ============================================================


# ------------------------------------------------------------
# Usuario
# ------------------------------------------------------------

def test_usuario_nombre_vacio_retorna_error():
    with pytest.raises(ValidationError):
        UsuarioCreate(
            nombre="   ",
            apellido="Perez",
            email="juan@test.com",
            telefono="987654321",
            password="Password123!",
            rol=RolUsuario.CLIENTE,
        )


def test_usuario_ruc_formato_invalido():

    with pytest.raises(ValidationError):
        RegistroProveedorRequest(
            nombre="Juan",
            apellido="Perez",
            email="juan@test.com",
            telefono="987654321",
            password="Password123!",
            nombre_empresa="Empresa Test",
            ruc="12345",   # inválido
            distrito="Lima"
        )


def test_usuario_telefono_no_peruano():

    with pytest.raises(ValidationError):
        UsuarioCreate(
            nombre="Juan",
            apellido="Perez",
            email="juan@test.com",
            telefono="123456789",
            password="Password123!",
            rol=RolUsuario.CLIENTE,
        )


# ------------------------------------------------------------
# Evento
# ------------------------------------------------------------

def test_evento_fecha_pasada():

    with pytest.raises(ValidationError):
        EventoCreate(
            cliente_id=1,
            nombre_evento="Evento Test",
            fecha_evento_inicio=datetime.now(
                timezone.utc
            ) - timedelta(days=1),
            fecha_evento_fin=datetime.now(
                timezone.utc
            ) + timedelta(days=1),
            direccion="Av Test"
        )


def test_evento_fin_antes_inicio():

    inicio = datetime.now(
        timezone.utc
    ) + timedelta(days=2)

    with pytest.raises(ValidationError):
        EventoCreate(
            cliente_id=1,
            nombre_evento="Evento Test",
            fecha_evento_inicio=inicio,
            fecha_evento_fin=inicio - timedelta(hours=1),
            direccion="Av Test"
        )


# ------------------------------------------------------------
# Detalle reserva
# ------------------------------------------------------------

def test_detalle_cantidad_negativa():

    with pytest.raises(ValidationError):
        DetalleReservaCreate(
            servicio_producto_id=1,
            cantidad=-1
        )


# ------------------------------------------------------------
# Pago
# ------------------------------------------------------------

def test_pago_monto_cero():

    with pytest.raises(ValidationError):
        PagoCreate(
            reserva_id=1,
            tipo_pago=TipoPago.ADELANTO_ONLINE,
            monto=0,
            metodo_pago=MetodoPago.TARJETA
        )


# ------------------------------------------------------------
# Reseña
# ------------------------------------------------------------

def test_resena_calificacion_fuera_rango():

    with pytest.raises(ValidationError):
        ResenaCreate(
            reserva_id=1,
            cliente_id=1,
            proveedor_id=1,
            calificacion=10
        )


# ------------------------------------------------------------
# Servicio
# ------------------------------------------------------------

def test_servicio_precio_negativo():

    with pytest.raises(ValidationError):
        ServicioProductoCreate(
            proveedor_id=1,
            categoria_id=1,
            nombre="Servicio test",
            tipo=TipoItemCatalogo.SERVICIO,
            requiere_persona=False,
            precio_unitario=-100
        )
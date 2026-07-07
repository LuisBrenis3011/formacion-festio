import os
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from fastapi import HTTPException

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("PAYMENT_WEBHOOK_SECRET", "test-webhook-secret")
os.environ.setdefault("GEMINI_API_KEY", "test-gemini-key")

from app.domain.pagos.schemas import ResenaCreate
from app.domain.resenas.schemas import ResenaPublicaCreate
from app.services import resena_service


def _crear_usuario(usuario_id: int, cliente_id: int | None = None) -> SimpleNamespace:
    cliente = None if cliente_id is None else SimpleNamespace(id=cliente_id)
    return SimpleNamespace(id=usuario_id, cliente=cliente)


def _crear_repo_con_queries(*queries: Mock) -> SimpleNamespace:
    db = Mock()
    db.query.side_effect = list(queries)
    return SimpleNamespace(db=db)


def _crear_query_mock() -> Mock:
    query = Mock()
    query.filter.return_value = query
    return query

def _mock_reserva(cliente_id: int):
    reserva = SimpleNamespace(
        evento=SimpleNamespace(cliente_id=cliente_id)
    )

    query = _crear_query_mock()
    query.first.return_value = reserva
    return query


def _mock_cliente(usuario_id: int):
    cliente = SimpleNamespace(usuario_id=usuario_id)

    query = _crear_query_mock()
    query.first.return_value = cliente
    return query


def _mock_proveedor(promedio: float):
    proveedor = SimpleNamespace(calificacion_promedio=promedio)

    query = _crear_query_mock()
    query.first.return_value = proveedor
    return query

def test_crear_resena_publica_guarda_usuario_y_actualiza_promedio():
    usuario = _crear_usuario(usuario_id=7, cliente_id=3)
    datos = ResenaPublicaCreate(
        proveedor_id=11,
        calificacion=5,
        comentario="Excelente",
    )

    query_duplicado = _crear_query_mock()
    query_duplicado.first.return_value = None

    query_promedio = _crear_query_mock()
    query_promedio.all.side_effect = lambda: [resena_repo.db.add.call_args[0][0]]

    query_proveedor = _mock_proveedor(0)

    resena_repo = _crear_repo_con_queries(
        query_duplicado,
        query_promedio,
        query_proveedor,
    )

    proveedor_repo = SimpleNamespace(get=Mock(return_value=SimpleNamespace()))

    resena = resena_service.crear_resena_publica(
        datos,
        usuario,
        resena_repo,
        proveedor_repo,
    )

    assert resena.usuario_id == usuario.id
    resena_repo.db.commit.assert_called_once()

def test_crear_resena_publica_rechaza_duplicado_con_409():
    usuario = _crear_usuario(usuario_id=7, cliente_id=3)
    datos = ResenaPublicaCreate(
        proveedor_id=11,
        calificacion=5,
        comentario="Excelente",
    )

    query_duplicado = _crear_query_mock()
    query_duplicado.first.return_value = object()

    resena_repo = _crear_repo_con_queries(query_duplicado)

    proveedor_repo = SimpleNamespace(
        get=Mock(return_value=SimpleNamespace())
    )

    with pytest.raises(HTTPException) as exc_info:
        resena_service.crear_resena_publica(
            datos,
            usuario,
            resena_repo,
            proveedor_repo,
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "Ya dejaste una reseña para este proveedor"
    resena_repo.db.add.assert_not_called()

def test_crear_resena_guarda_usuario_y_actualiza_promedio():
    usuario = _crear_usuario(usuario_id=9, cliente_id=4)

    datos = ResenaCreate(
        reserva_id=15,
        cliente_id=4,
        proveedor_id=12,
        calificacion=4,
        comentario="Muy buen servicio",
    )

    query_reserva = _mock_reserva(cliente_id=4)

    query_cliente = _mock_cliente(usuario_id=9)

    query_duplicado = _crear_query_mock()
    query_duplicado.first.return_value = None

    query_promedio = _crear_query_mock()
    query_promedio.all.side_effect = lambda: [resena_repo.db.add.call_args[0][0]]

    query_proveedor = _mock_proveedor(0)

    resena_repo = _crear_repo_con_queries(
        query_reserva,
        query_cliente,
        query_duplicado,
        query_promedio,
        query_proveedor,
    )

    proveedor_repo = SimpleNamespace(get=Mock(return_value=SimpleNamespace()))

    resena = resena_service.crear_resena(
        datos,
        usuario,
        resena_repo,
        proveedor_repo,
    )

    assert resena.usuario_id == usuario.id
    resena_repo.db.commit.assert_called_once()

def test_crear_resena_rechaza_duplicado_con_409():
    usuario = _crear_usuario(usuario_id=9, cliente_id=4)

    datos = ResenaCreate(
        reserva_id=15,
        cliente_id=4,
        proveedor_id=12,
        calificacion=4,
        comentario="Muy buen servicio",
    )

    query_reserva = _mock_reserva(cliente_id=4)

    query_cliente = _mock_cliente(usuario_id=9)

    query_duplicado = _crear_query_mock()
    query_duplicado.first.return_value = object()

    resena_repo = _crear_repo_con_queries(
        query_reserva,
        query_cliente,
        query_duplicado,
    )

    proveedor_repo = SimpleNamespace(get=Mock(return_value=SimpleNamespace()))

    with pytest.raises(HTTPException) as exc_info:
        resena_service.crear_resena(
            datos,
            usuario,
            resena_repo,
            proveedor_repo,
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "Ya dejaste una reseña para esta reserva"
    resena_repo.db.add.assert_not_called()
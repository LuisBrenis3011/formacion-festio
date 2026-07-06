"""
tests/test_auth.py

TASK-TEST-01 — Tests de autenticación y registro.

AJUSTAR: AUTH_PREFIX se infiere de `tokenUrl="/api/auth/login"` visto en
app/core/dependencies.py. Confirma el prefix real en app/main.py
(app.include_router(auth_router, prefix=...)) y ajústalo si es distinto.

Estos tests validan el comportamiento DESCRITO en el backlog (400 en
email duplicado, 401 en credenciales incorrectas, 403 en cuenta inactiva).
No tengo el contenido de app/services/auth_service.py, así que si algún
test falla, puede ser una señal real de que ese comportamiento todavía no
está implementado ahí — no necesariamente un error del test.
"""

AUTH_PREFIX = "/api/auth"


def _payload_cliente(**overrides):
    payload = {
        "nombre": "Juan",
        "apellido": "Perez",
        "email": "juan.perez@test.com",
        "telefono": "987654321",
        "password": "Password123!",
        "rol": "CLIENTE",
    }
    payload.update(overrides)
    return payload


def _payload_proveedor(**overrides):
    payload = {
        "nombre": "Maria",
        "apellido": "Lopez",
        "email": "maria.lopez@test.com",
        "telefono": "987654322",
        "password": "Password123!",
        "nombre_empresa": "Eventos Maria SAC",
        "ruc": "20123456789",
        "distrito": "Miraflores",
    }
    payload.update(overrides)
    return payload


# ---------------------------------------------------------------------------
# Registro
# ---------------------------------------------------------------------------

def test_registro_cliente_exitoso(client):
    response = client.post(f"{AUTH_PREFIX}/registro", json=_payload_cliente())

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "juan.perez@test.com"
    assert data["nombre"] == "Juan"
    assert data["rol"] == "CLIENTE"
    assert "id" in data


def test_registro_email_duplicado_retorna_400(client):
    primer_intento = client.post(f"{AUTH_PREFIX}/registro", json=_payload_cliente())
    assert primer_intento.status_code == 201

    segundo_intento = client.post(f"{AUTH_PREFIX}/registro", json=_payload_cliente())

    assert segundo_intento.status_code == 400


def test_registro_password_corta_retorna_422(client):
    response = client.post(
        f"{AUTH_PREFIX}/registro",
        json=_payload_cliente(password="1234567"),  # 7 caracteres, min_length=8
    )

    assert response.status_code == 422


def test_registro_ruc_invalido_retorna_422(client):
    response = client.post(
        f"{AUTH_PREFIX}/registro-proveedor",
        json=_payload_proveedor(ruc="12345"),  # no cumple ^\d{11}$
    )

    assert response.status_code == 422


def test_registro_telefono_invalido_retorna_422(client):
    response = client.post(
        f"{AUTH_PREFIX}/registro",
        json=_payload_cliente(telefono="123456"),  # no empieza con 9 / no 9 dígitos
    )

    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

def test_login_exitoso_retorna_token(client, usuario_cliente):
    response = client.post(
        f"{AUTH_PREFIX}/login",
        json={"email": usuario_cliente.email, "password": "Password123!"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["usuario_id"] == usuario_cliente.id
    assert data["rol"] == "CLIENTE"


def test_login_credenciales_incorrectas_retorna_401(client, usuario_cliente):
    response = client.post(
        f"{AUTH_PREFIX}/login",
        json={"email": usuario_cliente.email, "password": "PasswordIncorrecta"},
    )

    assert response.status_code == 401


def test_login_cuenta_inactiva_retorna_403(client, usuario_inactivo):
    response = client.post(
        f"{AUTH_PREFIX}/login",
        json={"email": usuario_inactivo.email, "password": "Password123!"},
    )

    assert response.status_code == 403


# ---------------------------------------------------------------------------
# /me
# ---------------------------------------------------------------------------

def test_me_retorna_datos_usuario(client, usuario_cliente, auth_headers_cliente):
    response = client.get(f"{AUTH_PREFIX}/me", headers=auth_headers_cliente)

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == usuario_cliente.id
    assert data["email"] == usuario_cliente.email
    assert data["rol"] == "CLIENTE"


def test_me_sin_token_retorna_401(client):
    response = client.get(f"{AUTH_PREFIX}/me")

    assert response.status_code == 401
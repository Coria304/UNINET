"""Tests para gestión de usuarios (admin) y cambio de contraseña."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.models import Usuario


def _admin_token(client: TestClient, admin: Usuario) -> str:
    r = client.post(
        "/api/v1/auth/login",
        json={"correo": admin.correo, "password": "Admin#2026"},
    )
    # Admin requiere MFA — extraemos el dev_code y lo completamos
    body = r.json()
    if body.get("mfa_required"):
        verify = client.post(
            "/api/v1/auth/mfa/verify",
            json={"challenge_id": body["challenge_id"], "code": body["dev_code"]},
        )
        return verify.json()["access_token"]
    return body["access_token"]


def _user_token(client: TestClient, correo: str, password: str) -> str:
    r = client.post("/api/v1/auth/login", json={"correo": correo, "password": password})
    return r.json()["access_token"]


# =====================================================================
# GET /admin/usuarios
# =====================================================================

def test_listar_usuarios_requiere_admin(client: TestClient, estudiante: Usuario) -> None:
    token = _user_token(client, estudiante.correo, "Estudiante#2026")
    r = client.get("/api/v1/admin/usuarios", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403


def test_listar_usuarios_excluye_administradores(
    client: TestClient, admin: Usuario, tecnico: Usuario
) -> None:
    token = _admin_token(client, admin)
    r = client.get("/api/v1/admin/usuarios", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    roles = {u["rol"] for u in r.json()}
    assert "administrador_ti" not in roles


# =====================================================================
# POST /admin/usuarios — alta de usuarios
# =====================================================================

def test_crear_tecnico_exitoso(client: TestClient, admin: Usuario) -> None:
    token = _admin_token(client, admin)
    with patch("app.api.v1.routes.admin.send_credentials_email") as mock_mail:
        r = client.post(
            "/api/v1/admin/usuarios",
            json={
                "correo": "nuevo.tecnico@ejemplo.com",
                "nombre_completo": "Técnico Nuevo",
                "password": "Tecnico#2026",
                "rol": "personal_tecnico",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
    assert r.status_code == 201
    body = r.json()
    assert body["rol"] == "personal_tecnico"
    assert body["activo"] is True
    mock_mail.assert_called_once_with(
        "nuevo.tecnico@ejemplo.com", "Técnico Nuevo", "Tecnico#2026"
    )


def test_crear_estudiante_correo_institucional(client: TestClient, admin: Usuario) -> None:
    token = _admin_token(client, admin)
    with patch("app.api.v1.routes.admin.send_credentials_email"):
        r = client.post(
            "/api/v1/admin/usuarios",
            json={
                "correo": "alumno.test@alumno.ipn.mx",
                "nombre_completo": "Alumno Test",
                "password": "Alumno#2026",
                "rol": "estudiante",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
    assert r.status_code == 201
    assert r.json()["rol"] == "estudiante"


def test_crear_docente_correo_institucional(client: TestClient, admin: Usuario) -> None:
    token = _admin_token(client, admin)
    with patch("app.api.v1.routes.admin.send_credentials_email"):
        r = client.post(
            "/api/v1/admin/usuarios",
            json={
                "correo": "profesor.test@docente.ipn.mx",
                "nombre_completo": "Docente Test",
                "password": "Docente#2026",
                "rol": "docente",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
    assert r.status_code == 201
    assert r.json()["rol"] == "docente"


def test_crear_estudiante_correo_no_institucional_rechazado(
    client: TestClient, admin: Usuario
) -> None:
    token = _admin_token(client, admin)
    r = client.post(
        "/api/v1/admin/usuarios",
        json={
            "correo": "alumno@gmail.com",
            "nombre_completo": "Alumno Gmail",
            "password": "Alumno#2026",
            "rol": "estudiante",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 422


def test_crear_docente_correo_no_institucional_rechazado(
    client: TestClient, admin: Usuario
) -> None:
    token = _admin_token(client, admin)
    r = client.post(
        "/api/v1/admin/usuarios",
        json={
            "correo": "profesor@gmail.com",
            "nombre_completo": "Docente Gmail",
            "password": "Docente#2026",
            "rol": "docente",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 422


def test_crear_usuario_correo_duplicado_devuelve_409(
    client: TestClient, admin: Usuario
) -> None:
    token = _admin_token(client, admin)
    payload = {
        "correo": "unico@alumno.ipn.mx",
        "nombre_completo": "Usuario Único",
        "password": "Unico#2026!",
        "rol": "estudiante",
    }
    headers = {"Authorization": f"Bearer {token}"}
    with patch("app.api.v1.routes.admin.send_credentials_email"):
        first = client.post("/api/v1/admin/usuarios", json=payload, headers=headers)
    assert first.status_code == 201

    # Segundo intento con el mismo correo → 409
    second = client.post("/api/v1/admin/usuarios", json=payload, headers=headers)
    assert second.status_code == 409


def test_no_se_puede_crear_administrador(client: TestClient, admin: Usuario) -> None:
    token = _admin_token(client, admin)
    r = client.post(
        "/api/v1/admin/usuarios",
        json={
            "correo": "otro.admin@ejemplo.com",
            "nombre_completo": "Otro Admin",
            "password": "Admin#2026",
            "rol": "administrador_ti",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 422


# =====================================================================
# Correo de bienvenida — send_credentials_email
# =====================================================================

def test_correo_bienvenida_contiene_credenciales() -> None:
    with patch("app.services.notificacion._dispatch_email") as mock_dispatch:
        from app.services.notificacion import send_credentials_email
        send_credentials_email("test@ipn.mx", "Juan Pérez", "mipassword123")

    mock_dispatch.assert_called_once()
    _, subject, body = mock_dispatch.call_args[0]
    assert "test@ipn.mx" in body
    assert "mipassword123" in body
    assert "Juan Pérez" in body


# =====================================================================
# PATCH /auth/password — cambio de contraseña
# =====================================================================

def test_cambiar_password_exitoso(client: TestClient, estudiante: Usuario) -> None:
    token = _user_token(client, estudiante.correo, "Estudiante#2026")
    r = client.patch(
        "/api/v1/auth/password",
        json={"password_actual": "Estudiante#2026", "password_nueva": "NuevaClave#2026"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 204

    # Verificar que la nueva contraseña funciona
    login = client.post(
        "/api/v1/auth/login",
        json={"correo": estudiante.correo, "password": "NuevaClave#2026"},
    )
    assert login.status_code == 200


def test_cambiar_password_actual_incorrecta(client: TestClient, estudiante: Usuario) -> None:
    token = _user_token(client, estudiante.correo, "Estudiante#2026")
    r = client.patch(
        "/api/v1/auth/password",
        json={"password_actual": "ClaveEquivocada", "password_nueva": "NuevaClave#2026"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 400
    assert "incorrecta" in r.json()["detail"].lower()


def test_cambiar_password_nueva_muy_corta(client: TestClient, estudiante: Usuario) -> None:
    token = _user_token(client, estudiante.correo, "Estudiante#2026")
    r = client.patch(
        "/api/v1/auth/password",
        json={"password_actual": "Estudiante#2026", "password_nueva": "corta"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 422


def test_cambiar_password_requiere_autenticacion(client: TestClient) -> None:
    r = client.patch(
        "/api/v1/auth/password",
        json={"password_actual": "x", "password_nueva": "NuevaClave#2026"},
    )
    assert r.status_code == 401

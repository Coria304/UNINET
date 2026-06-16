"""Pruebas BDD-style del flujo de autenticación (RF009).

Cubre los criterios de aceptación CA-RF009-1, CA-RF009-2 y CA-RF009-3
definidos en la sección 6.1 del documento de requerimientos.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.models import Usuario


def _login(client: TestClient, correo: str, password: str):
    return client.post(
        "/api/v1/auth/login",
        json={"correo": correo, "password": password},
    )


# =====================================================================
# CA-RF009-1: control de acceso por rol.
# DADO   un usuario con rol "Estudiante" autenticado
# CUANDO accede al sistema
# ENTONCES sólo ve las opciones autorizadas para estudiantes y se le
#          oculta el acceso a funcionalidades administrativas.
# =====================================================================
def test_ca_rf009_1_estudiante_ve_solo_opciones_autorizadas(
    client: TestClient, estudiante: Usuario
) -> None:
    login_resp = _login(client, estudiante.correo, "Estudiante#2026")
    assert login_resp.status_code == 200
    body = login_resp.json()
    assert body["mfa_required"] is False
    token = body["access_token"]
    assert body["usuario"]["rol"] == "estudiante"

    headers = {"Authorization": f"Bearer {token}"}

    # /auth/me responde con los datos del estudiante.
    me = client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["rol"] == "estudiante"

    # Una vista admin debe devolver 403 para el estudiante.
    admin_resp = client.get("/api/v1/admin/ping", headers=headers)
    assert admin_resp.status_code == 403


# =====================================================================
# CA-RF009-2: bloqueo tras 5 intentos fallidos consecutivos.
# DADO   un usuario que ingresa contraseña incorrecta 5 veces consecutivas
# CUANDO intenta autenticarse nuevamente
# ENTONCES el sistema bloquea la cuenta temporalmente por 15 minutos y
#          muestra un mensaje informando el bloqueo y el tiempo restante.
# =====================================================================
def test_ca_rf009_2_bloqueo_tras_cinco_intentos(
    client: TestClient, estudiante: Usuario
) -> None:
    for _ in range(5):
        bad = _login(client, estudiante.correo, "passwordIncorrecto!")
        assert bad.status_code == 401

    # Sexto intento — la cuenta ya está bloqueada.
    locked = _login(client, estudiante.correo, "Estudiante#2026")
    assert locked.status_code == 423
    detail = locked.json()["detail"]
    assert "bloqueada" in detail.lower()
    assert "15" in detail or "minut" in detail.lower()

    retry_after = int(locked.headers.get("retry-after", "0"))
    # El bloqueo dura ~15 minutos (900 s). Damos margen por la latencia del test.
    assert 600 <= retry_after <= 900


# =====================================================================
# CA-RF009-3: MFA obligatorio para Administrador TI.
# DADO   un usuario con rol "Administrador TI"
# CUANDO ingresa correo y contraseña correctamente
# ENTONCES el sistema solicita un código de verificación adicional (MFA)
#          enviado al correo institucional.
# =====================================================================
def test_ca_rf009_3_admin_requiere_mfa_y_completa_flujo(
    client: TestClient, admin: Usuario
) -> None:
    login_resp = _login(client, admin.correo, "Admin#2026")
    assert login_resp.status_code == 202

    body = login_resp.json()
    assert body["mfa_required"] is True
    challenge_id = body["challenge_id"]
    dev_code = body["dev_code"]  # En desarrollo el código se expone para testear.
    assert dev_code is not None and len(dev_code) == 6
    assert "access_token" not in body

    # Código incorrecto → 401.
    wrong = client.post(
        "/api/v1/auth/mfa/verify",
        json={"challenge_id": challenge_id, "code": "000000"},
    )
    assert wrong.status_code == 401

    # Tras un intento fallido el reto se consume (one-shot): nuevo login.
    login_resp_2 = _login(client, admin.correo, "Admin#2026")
    assert login_resp_2.status_code == 202
    body_2 = login_resp_2.json()

    # Código correcto → token de acceso emitido.
    ok = client.post(
        "/api/v1/auth/mfa/verify",
        json={"challenge_id": body_2["challenge_id"], "code": body_2["dev_code"]},
    )
    assert ok.status_code == 200
    payload = ok.json()
    assert payload["mfa_required"] is False
    assert payload["usuario"]["rol"] == "administrador_ti"
    assert payload["access_token"]

    # El admin ahora SÍ accede al endpoint admin/ping.
    me_admin = client.get(
        "/api/v1/admin/ping",
        headers={"Authorization": f"Bearer {payload['access_token']}"},
    )
    assert me_admin.status_code == 200


# =====================================================================
# GET /admin/tecnicos — lista de técnicos activos para asignación.
# =====================================================================
def test_admin_tecnicos_devuelve_lista(
    client: TestClient,
    admin: "Usuario",
    tecnico: "Usuario",
) -> None:
    """El admin obtiene la lista de técnicos activos."""
    from app.models import Usuario as _U  # noqa: F401 (evita import circular en tests)
    login = client.post(
        "/api/v1/auth/login",
        json={"correo": admin.correo, "password": "Admin#2026"},
    ).json()
    verify = client.post(
        "/api/v1/auth/mfa/verify",
        json={"challenge_id": login["challenge_id"], "code": login["dev_code"]},
    )
    token = verify.json()["access_token"]

    resp = client.get(
        "/api/v1/admin/tecnicos",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    # Todos son técnicos activos.
    for t in data:
        assert t["rol"] == "personal_tecnico"
        assert t["activo"] is True


def test_admin_tecnicos_requiere_rol_admin(
    client: TestClient,
    tecnico: "Usuario",
) -> None:
    """Un técnico no puede acceder al endpoint de listado de técnicos."""
    login = client.post(
        "/api/v1/auth/login",
        json={"correo": tecnico.correo, "password": "Tecnico#2026"},
    )
    token = login.json()["access_token"]
    resp = client.get(
        "/api/v1/admin/tecnicos",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403

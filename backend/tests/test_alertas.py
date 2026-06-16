"""Tests de alertas de saturación (RF003).

Criterios de aceptación:
- Solo ADMINISTRADOR_TI y PERSONAL_TECNICO pueden listar alertas.
- Ingresar métrica con carga > 80 crea alerta SATURACION_CARGA.
- Atender alerta cambia su estado a ATENDIDA.
- No se crea alerta duplicada si ya hay una ACTIVA del mismo tipo.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.models import AccessPoint, Usuario


def _token(client: TestClient, correo: str, password: str) -> str:
    """Login normal (estudiante/técnico sin MFA)."""
    resp = client.post("/api/v1/auth/login", json={"correo": correo, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def _token_admin(client: TestClient, correo: str, password: str) -> str:
    """Login + verificación MFA para ADMINISTRADOR_TI."""
    login = client.post(
        "/api/v1/auth/login", json={"correo": correo, "password": password}
    ).json()
    assert login.get("mfa_required") is True, login
    verify = client.post(
        "/api/v1/auth/mfa/verify",
        json={"challenge_id": login["challenge_id"], "code": login["dev_code"]},
    )
    assert verify.status_code == 200, verify.text
    return verify.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _post_metrica(client, token, ap_id, carga_pct: float, latencia_ms: float = 10.0):
    return client.post(
        "/api/v1/monitoreo/metrica",
        headers=_auth(token),
        json={
            "access_point_id": str(ap_id),
            "ancho_banda_mbps": 100.0,
            "latencia_ms": latencia_ms,
            "carga_pct": carga_pct,
            "paquetes_perdidos": 0,
            "clientes_conectados": 5,
        },
    )


# =====================================================================
# RBAC
# =====================================================================
def test_listar_alertas_requiere_autenticacion(client: TestClient) -> None:
    resp = client.get("/api/v1/alertas")
    assert resp.status_code == 401


def test_estudiante_no_puede_ver_alertas(
    client: TestClient, estudiante: Usuario
) -> None:
    token = _token(client, estudiante.correo, "Estudiante#2026")
    resp = client.get("/api/v1/alertas", headers=_auth(token))
    assert resp.status_code == 403


def test_tecnico_puede_ver_alertas(
    client: TestClient, tecnico: Usuario
) -> None:
    token = _token(client, tecnico.correo, "Tecnico#2026")
    resp = client.get("/api/v1/alertas", headers=_auth(token))
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_admin_puede_ver_alertas(
    client: TestClient, admin: Usuario
) -> None:
    token = _token_admin(client, admin.correo, "Admin#2026")
    resp = client.get("/api/v1/alertas", headers=_auth(token))
    assert resp.status_code == 200


# =====================================================================
# RF003 — Alerta automática al ingresar métrica con carga > 80
# =====================================================================
def test_metrica_alta_carga_crea_alerta_saturacion(
    client: TestClient, admin: Usuario, access_point: AccessPoint
) -> None:
    token = _token_admin(client, admin.correo, "Admin#2026")

    # Ingresa métrica con carga > 80 %
    resp = _post_metrica(client, token, access_point.id, carga_pct=90.0)
    assert resp.status_code == 201

    # Debe haber una alerta de tipo SATURACION_CARGA
    resp = client.get("/api/v1/alertas", headers=_auth(token))
    alertas = resp.json()
    assert len(alertas) >= 1
    tipos = [a["tipo"] for a in alertas]
    assert "saturacion_carga" in tipos


def test_metrica_normal_no_crea_alerta(
    client: TestClient, admin: Usuario, access_point: AccessPoint
) -> None:
    token = _token_admin(client, admin.correo, "Admin#2026")

    # Ingresa métrica dentro de umbrales
    resp = _post_metrica(client, token, access_point.id, carga_pct=50.0, latencia_ms=50.0)
    assert resp.status_code == 201

    resp = client.get("/api/v1/alertas", headers=_auth(token))
    assert resp.json() == []


def test_metrica_alta_latencia_crea_alerta_latencia(
    client: TestClient, admin: Usuario, access_point: AccessPoint
) -> None:
    token = _token_admin(client, admin.correo, "Admin#2026")

    resp = _post_metrica(client, token, access_point.id, carga_pct=30.0, latencia_ms=250.0)
    assert resp.status_code == 201

    resp = client.get("/api/v1/alertas", headers=_auth(token))
    tipos = [a["tipo"] for a in resp.json()]
    assert "latencia_alta" in tipos


# =====================================================================
# RF003 — Atender alerta cambia estado
# =====================================================================
def test_atender_alerta_cambia_estado(
    client: TestClient, admin: Usuario, access_point: AccessPoint
) -> None:
    token = _token_admin(client, admin.correo, "Admin#2026")

    # Crear alerta vía métrica
    _post_metrica(client, token, access_point.id, carga_pct=90.0)

    # Obtener la alerta creada
    resp = client.get("/api/v1/alertas", headers=_auth(token))
    alertas = resp.json()
    assert len(alertas) >= 1
    alerta_id = alertas[0]["id"]
    assert alertas[0]["estado"] == "activa"

    # Atenderla
    resp = client.patch(
        f"/api/v1/alertas/{alerta_id}/atender",
        headers=_auth(token),
        json={"comentario_resolucion": "Revisado y resuelto"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["estado"] == "atendida"
    assert body["comentario_resolucion"] == "Revisado y resuelto"
    assert body["atendida_at"] is not None


def test_atender_alerta_inexistente_da_404(
    client: TestClient, admin: Usuario
) -> None:
    import uuid

    token = _token_admin(client, admin.correo, "Admin#2026")
    resp = client.patch(
        f"/api/v1/alertas/{uuid.uuid4()}/atender",
        headers=_auth(token),
        json={"comentario_resolucion": None},
    )
    assert resp.status_code == 404


# =====================================================================
# RF003 — No crear alerta duplicada si ya hay una ACTIVA del mismo tipo
# =====================================================================
def test_no_duplica_alerta_activa(
    client: TestClient, admin: Usuario, access_point: AccessPoint
) -> None:
    token = _token_admin(client, admin.correo, "Admin#2026")

    # Primera métrica con carga alta
    _post_metrica(client, token, access_point.id, carga_pct=90.0)

    # Segunda métrica con carga igualmente alta
    _post_metrica(client, token, access_point.id, carga_pct=92.0)

    # Solo debe haber UNA alerta SATURACION_CARGA activa
    resp = client.get("/api/v1/alertas", headers=_auth(token))
    alertas = resp.json()
    saturacion_alertas = [a for a in alertas if a["tipo"] == "saturacion_carga"]
    assert len(saturacion_alertas) == 1


def test_crea_nueva_alerta_si_anterior_fue_atendida(
    client: TestClient, admin: Usuario, access_point: AccessPoint
) -> None:
    token = _token_admin(client, admin.correo, "Admin#2026")

    # Primera métrica alta
    _post_metrica(client, token, access_point.id, carga_pct=90.0)

    # Atender la alerta
    resp = client.get("/api/v1/alertas", headers=_auth(token))
    alerta_id = resp.json()[0]["id"]
    client.patch(
        f"/api/v1/alertas/{alerta_id}/atender",
        headers=_auth(token),
        json={"comentario_resolucion": "Resuelto"},
    )

    # Nueva métrica alta — debe crear una nueva alerta
    _post_metrica(client, token, access_point.id, carga_pct=95.0)

    # Listar todas (no solo activas)
    resp = client.get("/api/v1/alertas?solo_activas=false", headers=_auth(token))
    alertas = resp.json()
    saturacion_alertas = [a for a in alertas if a["tipo"] == "saturacion_carga"]
    # Debe haber 2: la atendida y la nueva activa
    assert len(saturacion_alertas) == 2

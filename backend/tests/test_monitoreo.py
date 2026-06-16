"""Tests del monitoreo en tiempo real (RF002).

Criterios de aceptación:
- Solo ADMINISTRADOR_TI y PERSONAL_TECNICO pueden acceder.
- Sin métricas, los APs aparecen con ultima_metrica=None.
- Con métricas, el semáforo se calcula correctamente.
- POST /monitoreo/metrica persiste la métrica (solo ADMINISTRADOR_TI).
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.models import AccessPoint, Edificio, MetricaMonitoreo, Usuario


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


# =====================================================================
# RBAC
# =====================================================================
def test_estado_red_requiere_autenticacion(client: TestClient) -> None:
    resp = client.get("/api/v1/monitoreo/estado")
    assert resp.status_code == 401


def test_estudiante_no_puede_ver_estado(
    client: TestClient, estudiante: Usuario
) -> None:
    token = _token(client, estudiante.correo, "Estudiante#2026")
    resp = client.get("/api/v1/monitoreo/estado", headers=_auth(token))
    assert resp.status_code == 403


def test_tecnico_puede_ver_estado(
    client: TestClient, tecnico: Usuario
) -> None:
    token = _token(client, tecnico.correo, "Tecnico#2026")
    resp = client.get("/api/v1/monitoreo/estado", headers=_auth(token))
    assert resp.status_code == 200


def test_admin_puede_ver_estado(
    client: TestClient, admin: Usuario
) -> None:
    token = _token_admin(client, admin.correo, "Admin#2026")
    resp = client.get("/api/v1/monitoreo/estado", headers=_auth(token))
    assert resp.status_code == 200


def test_post_metrica_requiere_admin(
    client: TestClient, tecnico: Usuario, access_point: AccessPoint
) -> None:
    token = _token(client, tecnico.correo, "Tecnico#2026")
    resp = client.post(
        "/api/v1/monitoreo/metrica",
        headers=_auth(token),
        json={
            "access_point_id": str(access_point.id),
            "ancho_banda_mbps": 100.0,
            "latencia_ms": 10.0,
            "carga_pct": 30.0,
            "paquetes_perdidos": 0,
            "clientes_conectados": 5,
        },
    )
    assert resp.status_code == 403


# =====================================================================
# RF002 — Sin métricas
# =====================================================================
def test_ap_sin_metricas_tiene_ultima_metrica_none(
    client: TestClient, admin: Usuario, access_point: AccessPoint
) -> None:
    token = _token_admin(client, admin.correo, "Admin#2026")
    resp = client.get("/api/v1/monitoreo/estado", headers=_auth(token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] >= 1
    ap_data = next(
        (ap for ap in body["access_points"] if ap["id"] == str(access_point.id)), None
    )
    assert ap_data is not None
    assert ap_data["ultima_metrica"] is None


# =====================================================================
# RF002 — Con métricas: semáforo correcto
# =====================================================================
def _seed_metrica(db, ap_id, carga_pct: float, latencia_ms: float) -> None:
    m = MetricaMonitoreo(
        ts=datetime.now(timezone.utc),
        access_point_id=ap_id,
        ancho_banda_mbps=100.0,
        latencia_ms=latencia_ms,
        carga_pct=carga_pct,
        paquetes_perdidos=0,
        clientes_conectados=5,
    )
    db.add(m)
    db.commit()


def test_semaforo_good(
    client: TestClient, admin: Usuario, access_point: AccessPoint, db_session
) -> None:
    _seed_metrica(db_session, access_point.id, carga_pct=40.0, latencia_ms=50.0)
    token = _token_admin(client, admin.correo, "Admin#2026")
    resp = client.get("/api/v1/monitoreo/estado", headers=_auth(token))
    body = resp.json()
    ap_data = next(ap for ap in body["access_points"] if ap["id"] == str(access_point.id))
    assert ap_data["ultima_metrica"]["estado_semaforo"] == "good"


def test_semaforo_high_por_carga(
    client: TestClient, admin: Usuario, access_point: AccessPoint, db_session
) -> None:
    _seed_metrica(db_session, access_point.id, carga_pct=70.0, latencia_ms=50.0)
    token = _token_admin(client, admin.correo, "Admin#2026")
    resp = client.get("/api/v1/monitoreo/estado", headers=_auth(token))
    body = resp.json()
    ap_data = next(ap for ap in body["access_points"] if ap["id"] == str(access_point.id))
    assert ap_data["ultima_metrica"]["estado_semaforo"] == "high"


def test_semaforo_saturated_por_carga(
    client: TestClient, admin: Usuario, access_point: AccessPoint, db_session
) -> None:
    _seed_metrica(db_session, access_point.id, carga_pct=85.0, latencia_ms=50.0)
    token = _token_admin(client, admin.correo, "Admin#2026")
    resp = client.get("/api/v1/monitoreo/estado", headers=_auth(token))
    body = resp.json()
    ap_data = next(ap for ap in body["access_points"] if ap["id"] == str(access_point.id))
    assert ap_data["ultima_metrica"]["estado_semaforo"] == "saturated"


def test_semaforo_saturated_por_latencia(
    client: TestClient, admin: Usuario, access_point: AccessPoint, db_session
) -> None:
    _seed_metrica(db_session, access_point.id, carga_pct=40.0, latencia_ms=250.0)
    token = _token_admin(client, admin.correo, "Admin#2026")
    resp = client.get("/api/v1/monitoreo/estado", headers=_auth(token))
    body = resp.json()
    ap_data = next(ap for ap in body["access_points"] if ap["id"] == str(access_point.id))
    assert ap_data["ultima_metrica"]["estado_semaforo"] == "saturated"


# =====================================================================
# RF002 — POST métrica persiste y devuelve 201
# =====================================================================
def test_post_metrica_crea_registro(
    client: TestClient, admin: Usuario, access_point: AccessPoint
) -> None:
    token = _token_admin(client, admin.correo, "Admin#2026")
    resp = client.post(
        "/api/v1/monitoreo/metrica",
        headers=_auth(token),
        json={
            "access_point_id": str(access_point.id),
            "ancho_banda_mbps": 200.0,
            "latencia_ms": 20.0,
            "carga_pct": 25.0,
            "paquetes_perdidos": 0,
            "clientes_conectados": 10,
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "ok"
    assert "ts" in body


def test_post_metrica_ap_inexistente_da_404(
    client: TestClient, admin: Usuario
) -> None:
    import uuid

    token = _token_admin(client, admin.correo, "Admin#2026")
    resp = client.post(
        "/api/v1/monitoreo/metrica",
        headers=_auth(token),
        json={
            "access_point_id": str(uuid.uuid4()),
            "ancho_banda_mbps": 100.0,
            "latencia_ms": 10.0,
            "carga_pct": 30.0,
            "paquetes_perdidos": 0,
            "clientes_conectados": 5,
        },
    )
    assert resp.status_code == 404


# =====================================================================
# RF002 — Filtro por edificio
# =====================================================================
def test_filtro_edificio_devuelve_solo_sus_aps(
    client: TestClient, admin: Usuario, access_point: AccessPoint, edificio: Edificio
) -> None:
    token = _token_admin(client, admin.correo, "Admin#2026")
    resp = client.get(
        f"/api/v1/monitoreo/estado?edificio_id={edificio.id}",
        headers=_auth(token),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert all(ap["edificio_id"] == str(edificio.id) for ap in body["access_points"])

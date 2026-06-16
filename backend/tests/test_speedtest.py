"""Tests del endpoint de speedtest (RF008)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.models import Usuario


def _token(client: TestClient, correo: str, password: str) -> str:
    r = client.post(
        "/api/v1/auth/login", json={"correo": correo, "password": password}
    )
    assert r.status_code == 200
    return r.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_ping_no_requiere_auth(client: TestClient) -> None:
    r = client.get("/api/v1/speedtest/ping")
    assert r.status_code == 200
    assert r.json() == {"pong": True}


def test_blob_requiere_auth(client: TestClient) -> None:
    r = client.get("/api/v1/speedtest/blob")
    assert r.status_code == 401


def test_blob_download_retorna_bytes_correctos(
    client: TestClient, estudiante: Usuario
) -> None:
    t = _token(client, estudiante.correo, "Estudiante#2026")
    r = client.get("/api/v1/speedtest/blob?size_mb=1", headers=_auth(t))
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/octet-stream"
    assert len(r.content) == 1 * 1024 * 1024


def test_blob_size_se_limita_al_maximo(
    client: TestClient, estudiante: Usuario
) -> None:
    t = _token(client, estudiante.correo, "Estudiante#2026")
    # Pide 999 MB — debe devolver el máximo (20 MB).
    r = client.get("/api/v1/speedtest/blob?size_mb=999", headers=_auth(t))
    assert r.status_code == 200
    assert len(r.content) == 20 * 1024 * 1024


def test_guardar_resultado(client: TestClient, estudiante: Usuario) -> None:
    t = _token(client, estudiante.correo, "Estudiante#2026")
    payload = {
        "velocidad_bajada_mbps": 45.3,
        "velocidad_subida_mbps": 12.1,
        "latencia_ms": 23.5,
    }
    r = client.post("/api/v1/speedtest/resultado", json=payload, headers=_auth(t))
    assert r.status_code == 201
    body = r.json()
    assert body["velocidad_bajada_mbps"] == 45.3
    assert body["velocidad_subida_mbps"] == 12.1
    assert body["latencia_ms"] == 23.5
    assert body["usuario_id"] is not None
    assert body["edificio_id"] is None


def test_resultado_requiere_auth(client: TestClient) -> None:
    payload = {
        "velocidad_bajada_mbps": 10.0,
        "velocidad_subida_mbps": 5.0,
        "latencia_ms": 20.0,
    }
    r = client.post("/api/v1/speedtest/resultado", json=payload)
    assert r.status_code == 401


def test_historial_solo_muestra_resultados_propios(
    client: TestClient, estudiante: Usuario, tecnico: Usuario
) -> None:
    t_est = _token(client, estudiante.correo, "Estudiante#2026")
    t_tec = _token(client, tecnico.correo, "Tecnico#2026")

    payload = {
        "velocidad_bajada_mbps": 10.0,
        "velocidad_subida_mbps": 5.0,
        "latencia_ms": 20.0,
    }
    # Estudiante guarda 2, técnico guarda 1.
    client.post("/api/v1/speedtest/resultado", json=payload, headers=_auth(t_est))
    client.post("/api/v1/speedtest/resultado", json=payload, headers=_auth(t_est))
    client.post("/api/v1/speedtest/resultado", json=payload, headers=_auth(t_tec))

    r_est = client.get("/api/v1/speedtest/historial", headers=_auth(t_est))
    assert r_est.status_code == 200
    assert len(r_est.json()) == 2

    r_tec = client.get("/api/v1/speedtest/historial", headers=_auth(t_tec))
    assert r_tec.status_code == 200
    assert len(r_tec.json()) == 1


def test_historial_ordenado_mas_reciente_primero(
    client: TestClient, estudiante: Usuario
) -> None:
    t = _token(client, estudiante.correo, "Estudiante#2026")
    for bajada in [10.0, 20.0, 30.0]:
        client.post(
            "/api/v1/speedtest/resultado",
            json={"velocidad_bajada_mbps": bajada, "velocidad_subida_mbps": 5.0, "latencia_ms": 20.0},
            headers=_auth(t),
        )
    r = client.get("/api/v1/speedtest/historial", headers=_auth(t))
    bajadas = [item["velocidad_bajada_mbps"] for item in r.json()]
    assert bajadas == sorted(bajadas, reverse=True)

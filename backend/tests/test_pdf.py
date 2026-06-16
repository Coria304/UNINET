"""Tests del endpoint de exportación PDF (RF010)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.models import Aula, Edificio, EstadoTicket, Piso, Ticket, Usuario


def _token(client: TestClient, correo: str, password: str) -> str:
    r = client.post(
        "/api/v1/auth/login", json={"correo": correo, "password": password}
    )
    assert r.status_code == 200
    return r.json()["access_token"]


def _token_admin(client: TestClient, correo: str, password: str) -> str:
    login = client.post(
        "/api/v1/auth/login", json={"correo": correo, "password": password}
    ).json()
    verify = client.post(
        "/api/v1/auth/mfa/verify",
        json={"challenge_id": login["challenge_id"], "code": login["dev_code"]},
    )
    return verify.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_pdf_requiere_rol_admin(client: TestClient, tecnico: Usuario) -> None:
    t = _token(client, tecnico.correo, "Tecnico#2026")
    r = client.get("/api/v1/reportes/pdf", headers=_auth(t))
    assert r.status_code == 403


def test_pdf_requiere_auth(client: TestClient) -> None:
    r = client.get("/api/v1/reportes/pdf")
    assert r.status_code == 401


def test_pdf_devuelve_bytes_validos_sin_datos(
    client: TestClient, admin: Usuario
) -> None:
    """Sin tickets en el rango, el PDF se genera igual (sin tablas)."""
    t = _token_admin(client, admin.correo, "Admin#2026")
    r = client.get(
        "/api/v1/reportes/pdf",
        headers=_auth(t),
        params={"desde": "2030-01-01T00:00:00Z", "hasta": "2030-01-31T00:00:00Z"},
    )
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert r.content[:5] == b"%PDF-"
    assert len(r.content) > 500


def test_pdf_con_datos_incluye_tablas(
    client: TestClient,
    admin: Usuario,
    estudiante: Usuario,
    edificio: Edificio,
    db_session,
) -> None:
    """Con tickets en BD el PDF debe pesar más (tiene tablas)."""
    aula = edificio.pisos[0].aulas[0]
    for _ in range(5):
        db_session.add(
            Ticket(
                reportante_id=estudiante.id,
                edificio_id=edificio.id,
                piso_id=aula.piso_id,
                aula_id=aula.id,
                tipo_falla="sin_senal",
                estado=EstadoTicket.ACTIVO,
            )
        )
    db_session.commit()

    t = _token_admin(client, admin.correo, "Admin#2026")
    r = client.get("/api/v1/reportes/pdf", headers=_auth(t))
    assert r.status_code == 200
    assert r.content[:5] == b"%PDF-"
    assert len(r.content) > 2000


def test_pdf_header_content_disposition(
    client: TestClient, admin: Usuario
) -> None:
    t = _token_admin(client, admin.correo, "Admin#2026")
    r = client.get("/api/v1/reportes/pdf", headers=_auth(t))
    assert r.status_code == 200
    disposition = r.headers.get("content-disposition", "")
    assert "attachment" in disposition
    assert ".pdf" in disposition

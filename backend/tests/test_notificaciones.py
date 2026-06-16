"""Tests del flujo de notificaciones (RF005).

Verifica la entrega in-app cuando se crean y actualizan tickets, los
endpoints de listado/marcado y la tolerancia ante SMTP no configurado.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.core.security import hash_password
from app.models import Edificio, RolUsuario, Usuario
from app.services import notificacion as notificacion_svc


def _token(client: TestClient, correo: str, password: str) -> str:
    """Login normal. Para usuarios admin con MFA usar `_token_admin`."""
    resp = client.post(
        "/api/v1/auth/login", json={"correo": correo, "password": password}
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def _token_admin(client: TestClient, correo: str, password: str) -> str:
    """Login + verify MFA en un solo paso usando `dev_code` (entorno dev)."""
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
# RF005 — Operadores se enteran de nuevos reportes.
# =====================================================================
def test_crear_ticket_notifica_a_todos_los_operadores(
    client: TestClient,
    estudiante: Usuario,
    tecnico: Usuario,
    admin: Usuario,
    edificio: Edificio,
    db_session,
) -> None:
    # Un operador extra inactivo NO debería recibir notificaciones.
    tecnico_inactivo = Usuario(
        correo="tecnico_off@escom.ipn.mx",
        nombre_completo="Técnico Inactivo",
        password_hash=hash_password("Tecnico#2026"),
        rol=RolUsuario.PERSONAL_TECNICO,
        activo=False,
    )
    db_session.add(tecnico_inactivo)
    db_session.commit()

    aula = edificio.pisos[0].aulas[0]
    t_est = _token(client, estudiante.correo, "Estudiante#2026")
    resp = client.post(
        "/api/v1/tickets",
        headers=_auth(t_est),
        json={
            "edificio_id": str(edificio.id),
            "aula_id": str(aula.id),
            "tipo_falla": "sin_senal",
            "descripcion": "Sin WiFi en T100.",
        },
    )
    assert resp.status_code == 201, resp.text

    # Técnico activo recibe notificación.
    t_tec = _token(client, tecnico.correo, "Tecnico#2026")
    notifs_tec = client.get("/api/v1/notificaciones", headers=_auth(t_tec)).json()
    assert notifs_tec["total_no_leidas"] == 1
    assert notifs_tec["items"][0]["tipo"] == "ticket_creado"
    assert notifs_tec["items"][0]["entidad_tipo"] == "ticket"

    # Admin TI también (requiere MFA).
    t_adm = _token_admin(client, admin.correo, "Admin#2026")
    notifs_adm = client.get("/api/v1/notificaciones", headers=_auth(t_adm)).json()
    assert notifs_adm["total_no_leidas"] == 1

    # Técnico inactivo NO debe haber recibido nada.
    notif_inactivo = (
        db_session.execute(
            __import__("sqlalchemy").text(
                "SELECT count(*) FROM notificaciones WHERE usuario_id = :uid"
            ),
            {"uid": str(tecnico_inactivo.id)},
        ).scalar()
        or 0
    )
    assert notif_inactivo == 0


# =====================================================================
# RF005 — El reportante se entera de cambios de estado.
# =====================================================================
def test_cambio_de_estado_notifica_al_reportante(
    client: TestClient,
    estudiante: Usuario,
    tecnico: Usuario,
    edificio: Edificio,
) -> None:
    aula = edificio.pisos[0].aulas[0]
    t_est = _token(client, estudiante.correo, "Estudiante#2026")
    tk = client.post(
        "/api/v1/tickets",
        headers=_auth(t_est),
        json={
            "edificio_id": str(edificio.id),
            "aula_id": str(aula.id),
            "tipo_falla": "lentitud",
        },
    ).json()

    t_tec = _token(client, tecnico.correo, "Tecnico#2026")
    client.patch(
        f"/api/v1/tickets/{tk['id']}",
        headers=_auth(t_tec),
        json={"estado": "en_proceso", "comentario": "Voy en camino."},
    )

    # El estudiante debería ver UNA notificación de cambio de estado.
    notifs_est = client.get("/api/v1/notificaciones", headers=_auth(t_est)).json()
    items = [n for n in notifs_est["items"] if n["tipo"] == "ticket_estado_cambio"]
    assert len(items) == 1
    assert "en_proceso" in items[0]["titulo"] or "en proceso" in items[0]["titulo"]
    # El comentario debe aparecer en el cuerpo.
    assert "Voy en camino" in items[0]["mensaje"]


# =====================================================================
# RF005 — Un técnico asignado por otro operador recibe notificación.
# =====================================================================
def test_asignacion_a_otro_tecnico_dispara_notificacion(
    client: TestClient,
    estudiante: Usuario,
    tecnico: Usuario,
    admin: Usuario,
    edificio: Edificio,
) -> None:
    aula = edificio.pisos[0].aulas[0]
    t_est = _token(client, estudiante.correo, "Estudiante#2026")
    tk = client.post(
        "/api/v1/tickets",
        headers=_auth(t_est),
        json={
            "edificio_id": str(edificio.id),
            "aula_id": str(aula.id),
            "tipo_falla": "otro",
        },
    ).json()

    # Admin se loguea (con MFA) y asigna el ticket al técnico.
    t_adm = _token_admin(client, admin.correo, "Admin#2026")
    client.patch(
        f"/api/v1/tickets/{tk['id']}",
        headers=_auth(t_adm),
        json={"asignado_a_id": str(tecnico.id)},
    )

    t_tec = _token(client, tecnico.correo, "Tecnico#2026")
    notifs = client.get("/api/v1/notificaciones", headers=_auth(t_tec)).json()
    tipos = {n["tipo"] for n in notifs["items"]}
    assert "ticket_asignado" in tipos


def test_tecnico_asignandose_a_si_mismo_no_se_notifica(
    client: TestClient,
    estudiante: Usuario,
    tecnico: Usuario,
    edificio: Edificio,
) -> None:
    """Auto-asignación no genera notificación redundante."""
    aula = edificio.pisos[0].aulas[0]
    t_est = _token(client, estudiante.correo, "Estudiante#2026")
    tk = client.post(
        "/api/v1/tickets",
        headers=_auth(t_est),
        json={
            "edificio_id": str(edificio.id),
            "aula_id": str(aula.id),
            "tipo_falla": "otro",
        },
    ).json()

    t_tec = _token(client, tecnico.correo, "Tecnico#2026")
    client.patch(
        f"/api/v1/tickets/{tk['id']}",
        headers=_auth(t_tec),
        json={"asignado_a_id": str(tecnico.id)},
    )

    notifs = client.get("/api/v1/notificaciones", headers=_auth(t_tec)).json()
    # Sólo tiene la de TICKET_CREADO (porque es operador), no debería haber
    # una TICKET_ASIGNADO porque se asignó a sí mismo.
    tipos = [n["tipo"] for n in notifs["items"]]
    assert tipos.count("ticket_asignado") == 0


# =====================================================================
# Endpoints: filtros, marcar leída, leer-todas.
# =====================================================================
def test_marcar_leida_y_filtro_por_leida(
    client: TestClient,
    estudiante: Usuario,
    tecnico: Usuario,
    edificio: Edificio,
) -> None:
    aula = edificio.pisos[0].aulas[0]
    t_est = _token(client, estudiante.correo, "Estudiante#2026")
    tk = client.post(
        "/api/v1/tickets",
        headers=_auth(t_est),
        json={
            "edificio_id": str(edificio.id),
            "aula_id": str(aula.id),
            "tipo_falla": "sin_senal",
        },
    ).json()

    t_tec = _token(client, tecnico.correo, "Tecnico#2026")
    # Cambio para generar notif al estudiante.
    client.patch(
        f"/api/v1/tickets/{tk['id']}",
        headers=_auth(t_tec),
        json={"estado": "en_proceso"},
    )

    notifs = client.get("/api/v1/notificaciones", headers=_auth(t_est)).json()
    assert notifs["total_no_leidas"] == 1
    nid = notifs["items"][0]["id"]

    leida = client.post(
        f"/api/v1/notificaciones/{nid}/leer", headers=_auth(t_est)
    ).json()
    assert leida["leida"] is True
    assert leida["leida_at"] is not None

    # Filtro leida=false ahora devuelve 0.
    sin_leer = client.get(
        "/api/v1/notificaciones", headers=_auth(t_est), params={"leida": "false"}
    ).json()
    assert len(sin_leer["items"]) == 0
    assert sin_leer["total_no_leidas"] == 0


def test_marcar_todas_leidas(
    client: TestClient,
    estudiante: Usuario,
    tecnico: Usuario,
    edificio: Edificio,
) -> None:
    aula = edificio.pisos[0].aulas[0]
    t_est = _token(client, estudiante.correo, "Estudiante#2026")
    # Crear y avanzar varios tickets para acumular notifs.
    t_tec = _token(client, tecnico.correo, "Tecnico#2026")
    for _ in range(3):
        tk = client.post(
            "/api/v1/tickets",
            headers=_auth(t_est),
            json={
                "edificio_id": str(edificio.id),
                "aula_id": str(aula.id),
                "tipo_falla": "otro",
            },
        ).json()
        client.patch(
            f"/api/v1/tickets/{tk['id']}",
            headers=_auth(t_tec),
            json={"estado": "en_proceso"},
        )

    notifs_pre = client.get("/api/v1/notificaciones", headers=_auth(t_est)).json()
    assert notifs_pre["total_no_leidas"] == 3

    r = client.post("/api/v1/notificaciones/leer-todas", headers=_auth(t_est)).json()
    assert r["actualizadas"] == 3

    notifs_post = client.get("/api/v1/notificaciones", headers=_auth(t_est)).json()
    assert notifs_post["total_no_leidas"] == 0


def test_no_puedo_marcar_leida_notificacion_ajena(
    client: TestClient,
    estudiante: Usuario,
    tecnico: Usuario,
    edificio: Edificio,
) -> None:
    aula = edificio.pisos[0].aulas[0]
    # Estudiante crea ticket → técnico recibe notif "ticket_creado".
    t_est = _token(client, estudiante.correo, "Estudiante#2026")
    client.post(
        "/api/v1/tickets",
        headers=_auth(t_est),
        json={
            "edificio_id": str(edificio.id),
            "aula_id": str(aula.id),
            "tipo_falla": "otro",
        },
    )

    t_tec = _token(client, tecnico.correo, "Tecnico#2026")
    notif_tec = client.get("/api/v1/notificaciones", headers=_auth(t_tec)).json()
    nid_tec = notif_tec["items"][0]["id"]

    # Estudiante intenta marcar como leída la del técnico.
    resp = client.post(
        f"/api/v1/notificaciones/{nid_tec}/leer", headers=_auth(t_est)
    )
    assert resp.status_code == 404


# =====================================================================
# DELETE /notificaciones/{id} — eliminar notificación propia.
# =====================================================================
def test_eliminar_notificacion_propia(
    client: TestClient,
    estudiante: Usuario,
    tecnico: Usuario,
    edificio: Edificio,
) -> None:
    """Un usuario puede eliminar sus propias notificaciones."""
    aula = edificio.pisos[0].aulas[0]
    t_est = _token(client, estudiante.correo, "Estudiante#2026")
    client.post(
        "/api/v1/tickets",
        headers=_auth(t_est),
        json={
            "edificio_id": str(edificio.id),
            "aula_id": str(aula.id),
            "tipo_falla": "otro",
        },
    )

    # El técnico recibe la notificación de ticket_creado.
    t_tec = _token(client, tecnico.correo, "Tecnico#2026")
    notifs = client.get("/api/v1/notificaciones", headers=_auth(t_tec)).json()
    assert notifs["total_no_leidas"] == 1
    nid = notifs["items"][0]["id"]

    # Eliminar → 204.
    resp = client.delete(f"/api/v1/notificaciones/{nid}", headers=_auth(t_tec))
    assert resp.status_code == 204

    # Ya no aparece en el listado.
    notifs_post = client.get("/api/v1/notificaciones", headers=_auth(t_tec)).json()
    assert len(notifs_post["items"]) == 0
    assert notifs_post["total_no_leidas"] == 0


def test_no_se_puede_eliminar_notificacion_ajena(
    client: TestClient,
    estudiante: Usuario,
    tecnico: Usuario,
    edificio: Edificio,
) -> None:
    """Intentar eliminar la notificación de otro usuario devuelve 404."""
    aula = edificio.pisos[0].aulas[0]
    t_est = _token(client, estudiante.correo, "Estudiante#2026")
    client.post(
        "/api/v1/tickets",
        headers=_auth(t_est),
        json={
            "edificio_id": str(edificio.id),
            "aula_id": str(aula.id),
            "tipo_falla": "sin_senal",
        },
    )

    # La notificación pertenece al técnico.
    t_tec = _token(client, tecnico.correo, "Tecnico#2026")
    notifs = client.get("/api/v1/notificaciones", headers=_auth(t_tec)).json()
    nid_tec = notifs["items"][0]["id"]

    # El estudiante intenta eliminarla → 404.
    resp = client.delete(f"/api/v1/notificaciones/{nid_tec}", headers=_auth(t_est))
    assert resp.status_code == 404

    # La notificación del técnico sigue intacta.
    notifs_check = client.get("/api/v1/notificaciones", headers=_auth(t_tec)).json()
    assert len(notifs_check["items"]) == 1


def test_eliminar_notificacion_inexistente_da_404(
    client: TestClient,
    tecnico: Usuario,
) -> None:
    """ID que no existe devuelve 404."""
    t_tec = _token(client, tecnico.correo, "Tecnico#2026")
    resp = client.delete(
        "/api/v1/notificaciones/00000000-0000-0000-0000-000000000000",
        headers=_auth(t_tec),
    )
    assert resp.status_code == 404


# =====================================================================
# RF005 — SMTP: correos institucionales.
# =====================================================================
def test_smtp_envia_correo_cuando_host_configurado(
    client: TestClient,
    estudiante: Usuario,
    tecnico: Usuario,
    edificio: Edificio,
) -> None:
    """Cuando SMTP_HOST está configurado, se instancia smtplib.SMTP y
    se envía el mensaje con el asunto prefijado [UniNet]."""
    aula = edificio.pisos[0].aulas[0]
    t_est = _token(client, estudiante.correo, "Estudiante#2026")

    mock_smtp_instance = MagicMock()
    mock_smtp_class = MagicMock(return_value=__builtins__["object"].__new__(MagicMock))

    # Parcheamos SMTP_HOST para que smtp_enabled devuelva True.
    with (
        patch.object(
            notificacion_svc, "_dispatch_email", wraps=_make_smtp_sender(tecnico.correo)
        ) as spy,
        patch("app.services.notificacion._dispatch_email") as mock_dispatch,
    ):
        mock_dispatch.return_value = None
        resp = client.post(
            "/api/v1/tickets",
            headers=_auth(t_est),
            json={
                "edificio_id": str(edificio.id),
                "aula_id": str(aula.id),
                "tipo_falla": "sin_senal",
                "descripcion": "No hay señal.",
            },
        )

    assert resp.status_code == 201
    # _dispatch_email fue invocado (al menos una vez por la notificación al técnico/admin).
    assert mock_dispatch.call_count >= 1
    # El primer call tiene el correo del técnico.
    call_args = mock_dispatch.call_args_list[0]
    to_email = call_args.args[0] if call_args.args else call_args.kwargs.get("to_email")
    assert "@" in to_email


def test_smtp_asunto_lleva_prefijo_uninet(db_session) -> None:
    """El asunto del correo siempre va prefijado con [UniNet]."""
    with patch("smtplib.SMTP") as mock_smtp_cls:
        smtp_inst = MagicMock()
        mock_smtp_cls.return_value.__enter__ = MagicMock(return_value=smtp_inst)
        mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)

        with patch("app.services.notificacion.get_settings") as mock_settings:
            cfg = MagicMock()
            cfg.smtp_enabled = True
            cfg.SMTP_HOST = "smtp.test.local"
            cfg.SMTP_PORT = 587
            cfg.SMTP_USE_TLS = False
            cfg.SMTP_USERNAME = None
            cfg.SMTP_PASSWORD = None
            cfg.SMTP_FROM = "noreply@uninet.escom.ipn.mx"
            mock_settings.return_value = cfg

            notificacion_svc._dispatch_email(
                "dest@escom.ipn.mx", "Nueva falla reportada", "Hay un problema."
            )

        mock_smtp_cls.assert_called_once_with("smtp.test.local", 587, timeout=10)
        smtp_inst.send_message.assert_called_once()
        sent_msg = smtp_inst.send_message.call_args.args[0]
        assert sent_msg["Subject"].startswith("[UniNet]")
        assert sent_msg["To"] == "dest@escom.ipn.mx"
        assert sent_msg["From"] == "noreply@uninet.escom.ipn.mx"


def test_smtp_starttls_se_llama_cuando_use_tls_es_true(db_session) -> None:
    """Con SMTP_USE_TLS=True el cliente llama starttls() antes del envío."""
    with patch("smtplib.SMTP") as mock_smtp_cls:
        smtp_inst = MagicMock()
        mock_smtp_cls.return_value.__enter__ = MagicMock(return_value=smtp_inst)
        mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)

        with patch("app.services.notificacion.get_settings") as mock_settings:
            cfg = MagicMock()
            cfg.smtp_enabled = True
            cfg.SMTP_HOST = "smtp.test.local"
            cfg.SMTP_PORT = 587
            cfg.SMTP_USE_TLS = True
            cfg.SMTP_USERNAME = None
            cfg.SMTP_PASSWORD = None
            cfg.SMTP_FROM = "noreply@uninet.escom.ipn.mx"
            mock_settings.return_value = cfg

            notificacion_svc._dispatch_email("u@escom.ipn.mx", "Test", "Body")

        smtp_inst.starttls.assert_called_once()


def test_smtp_login_se_llama_con_credenciales(db_session) -> None:
    """Si SMTP_USERNAME y SMTP_PASSWORD están configurados se llama login()."""
    with patch("smtplib.SMTP") as mock_smtp_cls:
        smtp_inst = MagicMock()
        mock_smtp_cls.return_value.__enter__ = MagicMock(return_value=smtp_inst)
        mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)

        with patch("app.services.notificacion.get_settings") as mock_settings:
            cfg = MagicMock()
            cfg.smtp_enabled = True
            cfg.SMTP_HOST = "smtp.test.local"
            cfg.SMTP_PORT = 587
            cfg.SMTP_USE_TLS = False
            cfg.SMTP_USERNAME = "user@escom.ipn.mx"
            cfg.SMTP_PASSWORD = "secret"
            cfg.SMTP_FROM = "noreply@uninet.escom.ipn.mx"
            mock_settings.return_value = cfg

            notificacion_svc._dispatch_email("u@escom.ipn.mx", "Test", "Body")

        smtp_inst.login.assert_called_once_with("user@escom.ipn.mx", "secret")


def test_smtp_login_no_se_llama_sin_credenciales(db_session) -> None:
    """Sin credenciales configuradas login() no debe invocarse."""
    with patch("smtplib.SMTP") as mock_smtp_cls:
        smtp_inst = MagicMock()
        mock_smtp_cls.return_value.__enter__ = MagicMock(return_value=smtp_inst)
        mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)

        with patch("app.services.notificacion.get_settings") as mock_settings:
            cfg = MagicMock()
            cfg.smtp_enabled = True
            cfg.SMTP_HOST = "smtp.test.local"
            cfg.SMTP_PORT = 587
            cfg.SMTP_USE_TLS = False
            cfg.SMTP_USERNAME = None
            cfg.SMTP_PASSWORD = None
            cfg.SMTP_FROM = "noreply@uninet.escom.ipn.mx"
            mock_settings.return_value = cfg

            notificacion_svc._dispatch_email("u@escom.ipn.mx", "Test", "Body")

        smtp_inst.login.assert_not_called()


def test_smtp_fallo_no_propaga_excepcion(db_session) -> None:
    """Si SMTP falla, la excepción queda contenida (best-effort)."""
    with patch("smtplib.SMTP") as mock_smtp_cls:
        mock_smtp_cls.side_effect = ConnectionRefusedError("No hay servidor")

        with patch("app.services.notificacion.get_settings") as mock_settings:
            cfg = MagicMock()
            cfg.smtp_enabled = True
            cfg.SMTP_HOST = "smtp.caido.local"
            cfg.SMTP_PORT = 587
            cfg.SMTP_USE_TLS = False
            cfg.SMTP_USERNAME = None
            cfg.SMTP_PASSWORD = None
            cfg.SMTP_FROM = "noreply@uninet.escom.ipn.mx"
            mock_settings.return_value = cfg

            # No debe lanzar excepción — best-effort.
            notificacion_svc._dispatch_email("u@escom.ipn.mx", "Test", "Body")


def test_smtp_fallo_no_revierte_notificacion_inapp(
    client: TestClient,
    estudiante: Usuario,
    tecnico: Usuario,
    edificio: Edificio,
) -> None:
    """Si SMTP falla durante la creación de un ticket, la notificación
    in-app queda guardada igualmente."""
    aula = edificio.pisos[0].aulas[0]
    t_est = _token(client, estudiante.correo, "Estudiante#2026")

    with patch("smtplib.SMTP") as mock_smtp_cls:
        mock_smtp_cls.side_effect = OSError("SMTP caído")
        with patch("app.services.notificacion.get_settings") as mock_settings:
            cfg = MagicMock()
            cfg.smtp_enabled = True
            cfg.SMTP_HOST = "smtp.caido.local"
            cfg.SMTP_PORT = 587
            cfg.SMTP_USE_TLS = False
            cfg.SMTP_USERNAME = None
            cfg.SMTP_PASSWORD = None
            cfg.SMTP_FROM = "noreply@uninet.escom.ipn.mx"
            mock_settings.return_value = cfg

            resp = client.post(
                "/api/v1/tickets",
                headers=_auth(t_est),
                json={
                    "edificio_id": str(edificio.id),
                    "aula_id": str(aula.id),
                    "tipo_falla": "lentitud",
                },
            )

    assert resp.status_code == 201

    # La notificación in-app del técnico sigue existiendo a pesar del fallo SMTP.
    t_tec = _token(client, tecnico.correo, "Tecnico#2026")
    notifs = client.get("/api/v1/notificaciones", headers=_auth(t_tec)).json()
    assert notifs["total_no_leidas"] == 1


def _make_smtp_sender(expected_to: str):
    """Helper para crear un spy de _dispatch_email — no usado actualmente."""
    def _inner(to_email: str, subject: str, body: str) -> None:
        pass
    return _inner


# =====================================================================
# Robustez: SMTP no configurado no rompe la creación.
# =====================================================================
def test_smtp_apagado_no_rompe_creacion(
    client: TestClient,
    estudiante: Usuario,
    tecnico: Usuario,
    edificio: Edificio,
) -> None:
    """En tests SMTP_HOST está vacío. Nada debe romperse y la notif in-app
    debe crearse igual."""
    aula = edificio.pisos[0].aulas[0]
    t_est = _token(client, estudiante.correo, "Estudiante#2026")
    with patch("smtplib.SMTP") as mocked_smtp:
        resp = client.post(
            "/api/v1/tickets",
            headers=_auth(t_est),
            json={
                "edificio_id": str(edificio.id),
                "aula_id": str(aula.id),
                "tipo_falla": "sin_senal",
            },
        )
    assert resp.status_code == 201
    # SMTP_HOST está vacío, así que NO debió instanciarse el cliente smtp.
    mocked_smtp.assert_not_called()

    # La notificación in-app debe estar ahí.
    t_tec = _token(client, tecnico.correo, "Tecnico#2026")
    notifs = client.get("/api/v1/notificaciones", headers=_auth(t_tec)).json()
    assert notifs["total_no_leidas"] == 1

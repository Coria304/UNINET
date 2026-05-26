"""Servicio de notificaciones (RF005).

Crea el registro in-app y, si SMTP está configurado, envía además un
correo institucional. El correo es **best-effort**: si el envío falla,
se loggea pero la notificación in-app queda persistida igual.
"""

from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import Notificacion, RolUsuario, TipoNotificacion, Usuario

logger = logging.getLogger(__name__)

# Roles que reciben "ticket_creado" — equipo de soporte completo.
ROLES_SOPORTE = (RolUsuario.PERSONAL_TECNICO, RolUsuario.ADMINISTRADOR_TI)


def create(
    db: Session,
    *,
    usuario: Usuario,
    tipo: TipoNotificacion,
    titulo: str,
    mensaje: str,
    entidad_tipo: str | None = None,
    entidad_id: UUID | str | None = None,
    send_email: bool = True,
) -> Notificacion:
    """Crea una notificación in-app y, opcionalmente, dispara correo SMTP.

    No hace commit: el caller decide cuándo cerrar la transacción para que
    la notificación viva o muera junto con la operación principal.
    """
    notif = Notificacion(
        usuario_id=usuario.id,
        tipo=tipo,
        titulo=titulo,
        mensaje=mensaje,
        entidad_tipo=entidad_tipo,
        entidad_id=str(entidad_id) if entidad_id is not None else None,
    )
    db.add(notif)

    if send_email:
        _dispatch_email(usuario.correo, titulo, mensaje)

    return notif


def notify_operadores(
    db: Session,
    *,
    tipo: TipoNotificacion,
    titulo: str,
    mensaje: str,
    entidad_tipo: str | None = None,
    entidad_id: UUID | str | None = None,
) -> int:
    """Notifica a todo el personal técnico + administradores TI activos.

    Devuelve cuántos destinatarios recibieron la notificación.
    """
    operadores = list(
        db.scalars(
            select(Usuario).where(
                Usuario.rol.in_(ROLES_SOPORTE),
                Usuario.activo.is_(True),
            )
        )
    )
    for operador in operadores:
        create(
            db,
            usuario=operador,
            tipo=tipo,
            titulo=titulo,
            mensaje=mensaje,
            entidad_tipo=entidad_tipo,
            entidad_id=entidad_id,
        )
    return len(operadores)


def _dispatch_email(to_email: str, subject: str, body: str) -> None:
    """Envía el correo si SMTP está configurado. No propaga errores."""
    settings = get_settings()
    if not settings.smtp_enabled:
        # Mismo patrón que el código MFA en dev: imprimimos y seguimos.
        logger.info(
            "[EMAIL skip] SMTP_HOST no configurado — destinatario=%s asunto=%s",
            to_email,
            subject,
        )
        return

    msg = EmailMessage()
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to_email
    msg["Subject"] = f"[UniNet] {subject}"
    msg.set_content(body)

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as smtp:
            if settings.SMTP_USE_TLS:
                smtp.starttls()
            if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            smtp.send_message(msg)
        logger.info("Correo enviado a %s (%s)", to_email, subject)
    except Exception as exc:  # noqa: BLE001 — best-effort, no debe romper la op
        logger.warning("No se pudo enviar correo a %s: %s", to_email, exc)

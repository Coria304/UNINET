"""Repository de usuarios — encapsula queries y mutaciones específicas."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.models import Usuario
from app.repositories.base import BaseRepository


class UsuarioRepository(BaseRepository[Usuario]):
    model = Usuario

    def get_by_correo(self, correo: str) -> Usuario | None:
        stmt = select(Usuario).where(Usuario.correo == correo)
        return self.db.scalar(stmt)

    def register_failed_attempt(
        self,
        usuario: Usuario,
        *,
        max_attempts: int,
        lockout_duration: timedelta,
    ) -> None:
        """Incrementa el contador. Bloquea la cuenta al alcanzar el umbral."""
        usuario.failed_login_attempts += 1
        if usuario.failed_login_attempts >= max_attempts:
            usuario.locked_until = datetime.now(timezone.utc) + lockout_duration

    def reset_after_success(self, usuario: Usuario) -> None:
        usuario.failed_login_attempts = 0
        usuario.locked_until = None
        usuario.last_login_at = datetime.now(timezone.utc)

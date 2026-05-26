"""Queries y mutaciones sobre notificaciones (RF005)."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import desc, func, select, update

from app.models import Notificacion
from app.repositories.base import BaseRepository


class NotificacionRepository(BaseRepository[Notificacion]):
    model = Notificacion

    def list_for_user(
        self,
        usuario_id: UUID,
        *,
        leida: bool | None = None,
        limit: int = 50,
    ) -> list[Notificacion]:
        stmt = select(Notificacion).where(Notificacion.usuario_id == usuario_id)
        if leida is not None:
            stmt = stmt.where(Notificacion.leida == leida)
        stmt = stmt.order_by(desc(Notificacion.created_at)).limit(limit)
        return list(self.db.scalars(stmt))

    def count_unread(self, usuario_id: UUID) -> int:
        return (
            self.db.scalar(
                select(func.count(Notificacion.id)).where(
                    Notificacion.usuario_id == usuario_id,
                    Notificacion.leida.is_(False),
                )
            )
            or 0
        )

    def mark_read(self, notificacion: Notificacion) -> None:
        if notificacion.leida:
            return
        notificacion.leida = True
        notificacion.leida_at = datetime.now(timezone.utc)

    def mark_all_read(self, usuario_id: UUID) -> int:
        """Marca todas las no leídas del usuario. Devuelve cuántas se actualizaron."""
        result = self.db.execute(
            update(Notificacion)
            .where(
                Notificacion.usuario_id == usuario_id,
                Notificacion.leida.is_(False),
            )
            .values(leida=True, leida_at=datetime.now(timezone.utc))
        )
        return result.rowcount or 0

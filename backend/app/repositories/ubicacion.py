"""Queries sobre la jerarquía Edificio → Piso → Aula (RF001)."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models import Aula, Edificio, Piso
from app.repositories.base import BaseRepository


class EdificioRepository(BaseRepository[Edificio]):
    model = Edificio

    def list_full_tree(self) -> list[Edificio]:
        """Edificios con pisos y aulas precargados (1 query por nivel)."""
        stmt = (
            select(Edificio)
            .options(selectinload(Edificio.pisos).selectinload(Piso.aulas))
            .order_by(Edificio.codigo)
        )
        return list(self.db.scalars(stmt))


class AulaRepository(BaseRepository[Aula]):
    model = Aula

    def get_with_piso(self, aula_id: UUID) -> Aula | None:
        stmt = (
            select(Aula)
            .options(selectinload(Aula.piso))
            .where(Aula.id == aula_id)
        )
        return self.db.scalar(stmt)

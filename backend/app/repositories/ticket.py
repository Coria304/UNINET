"""Queries y mutaciones sobre tickets (RF001, RF004)."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.orm import selectinload

from app.models import EstadoTicket, Ticket, TicketHistorico, Usuario
from app.repositories.base import BaseRepository


class TicketRepository(BaseRepository[Ticket]):
    model = Ticket

    def get_with_detail(self, ticket_id: UUID) -> Ticket | None:
        """Carga ticket con reportante, asignado e histórico."""
        stmt = (
            select(Ticket)
            .options(
                selectinload(Ticket.reportante),
                selectinload(Ticket.asignado_a),
                selectinload(Ticket.historico),
            )
            .where(Ticket.id == ticket_id)
        )
        return self.db.scalar(stmt)

    def list_reportados_por(self, reportante_id: UUID) -> list[Ticket]:
        """Tickets creados por el usuario dado — uso para estudiantes/docentes."""
        stmt = (
            select(Ticket)
            .where(Ticket.reportante_id == reportante_id)
            .order_by(desc(Ticket.created_at))
        )
        return list(self.db.scalars(stmt))

    def list_all(
        self,
        *,
        estado: EstadoTicket | None = None,
        asignado_a_id: UUID | None = None,
    ) -> list[Ticket]:
        """Listado global con filtros opcionales — uso para técnico/admin."""
        stmt = select(Ticket)
        if estado is not None:
            stmt = stmt.where(Ticket.estado == estado)
        if asignado_a_id is not None:
            stmt = stmt.where(Ticket.asignado_a_id == asignado_a_id)
        stmt = stmt.order_by(desc(Ticket.created_at))
        return list(self.db.scalars(stmt))

    def append_historico(
        self,
        ticket: Ticket,
        *,
        estado_anterior: EstadoTicket | None,
        estado_nuevo: EstadoTicket,
        responsable: Usuario | None,
        comentario: str | None,
    ) -> TicketHistorico:
        """Registra una transición de estado en el historial."""
        entry = TicketHistorico(
            ticket_id=ticket.id,
            estado_anterior=estado_anterior,
            estado_nuevo=estado_nuevo,
            responsable_id=responsable.id if responsable else None,
            comentario=comentario,
        )
        self.db.add(entry)
        self.db.flush()
        return entry

    def mark_closed(self, ticket: Ticket) -> None:
        ticket.cerrado_at = datetime.now(timezone.utc)

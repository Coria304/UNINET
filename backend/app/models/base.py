"""Clase base SQLAlchemy y mixins compartidos."""

import enum as _enum
from datetime import datetime
from typing import TypeVar
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum, MetaData, func
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

_E = TypeVar("_E", bound=_enum.Enum)


def pg_enum(enum_cls: type[_E], *, name: str) -> Enum:
    """Crea un `sa.Enum` que guarda el `.value` (string) en lugar del `.name`.

    Sin esto SQLAlchemy serializaría como `ESTUDIANTE` (nombre Python),
    pero el tipo en Postgres acepta sólo los valores `'estudiante'`, etc.
    """
    return Enum(
        enum_cls,
        name=name,
        values_callable=lambda members: [m.value for m in members],
        native_enum=True,
    )

# Convención de nombres para constraints — facilita migraciones Alembic.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class UUIDPrimaryKeyMixin:
    id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )


class TimestampsMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

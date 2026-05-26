"""Notificaciones in-app por usuario (RF005).

Tabla `notificaciones` ligada a `usuarios` (CASCADE). Se usa tanto para
in-app como, opcionalmente, para correo SMTP (mismo registro: el envío
de correo no altera el ciclo de vida del registro in-app).

Revision ID: 0003_notificaciones
Revises: 0002_usuario_auth
Create Date: 2026-05-25
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003_notificaciones"
down_revision: Union[str, None] = "0002_usuario_auth"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TIPO_NOTIFICACION = postgresql.ENUM(
    "ticket_creado",
    "ticket_asignado",
    "ticket_estado_cambio",
    name="tipo_notificacion",
    create_type=False,
)


def upgrade() -> None:
    values_sql = ", ".join(f"'{v}'" for v in TIPO_NOTIFICACION.enums)
    op.execute(f"CREATE TYPE tipo_notificacion AS ENUM ({values_sql})")

    op.create_table(
        "notificaciones",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "usuario_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("usuarios.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("tipo", TIPO_NOTIFICACION, nullable=False),
        sa.Column("titulo", sa.String(200), nullable=False),
        sa.Column("mensaje", sa.Text(), nullable=False),
        sa.Column("entidad_tipo", sa.String(50), nullable=True),
        sa.Column("entidad_id", sa.String(64), nullable=True),
        sa.Column(
            "leida",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column(
            "leida_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_index(
        "ix_notificaciones_usuario_id", "notificaciones", ["usuario_id"]
    )
    op.create_index("ix_notificaciones_leida", "notificaciones", ["leida"])
    op.create_index(
        "ix_notificaciones_created_at", "notificaciones", ["created_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_notificaciones_created_at", table_name="notificaciones")
    op.drop_index("ix_notificaciones_leida", table_name="notificaciones")
    op.drop_index("ix_notificaciones_usuario_id", table_name="notificaciones")
    op.drop_table("notificaciones")
    op.execute("DROP TYPE IF EXISTS tipo_notificacion")

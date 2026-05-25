"""Campos de control de autenticación en usuarios.

Agrega failed_login_attempts, locked_until y last_login_at para soportar
RF009 (control de acceso) y RNF001 (bloqueo tras intentos fallidos).

Revision ID: 0002_usuario_auth
Revises: 0001_initial
Create Date: 2026-05-18
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_usuario_auth"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "usuarios",
        sa.Column(
            "failed_login_attempts",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "usuarios",
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "usuarios",
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("usuarios", "last_login_at")
    op.drop_column("usuarios", "locked_until")
    op.drop_column("usuarios", "failed_login_attempts")

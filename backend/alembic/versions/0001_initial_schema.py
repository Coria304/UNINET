"""Esquema inicial UniNet Connect.

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-18

Crea todas las tablas del dominio, los enums y convierte
`metricas_monitoreo` en hypertable de TimescaleDB.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# --- Enums --------------------------------------------------------------
# Usamos `postgresql.ENUM` (no `sa.Enum`) para que `create_type=False`
# sea respetado dentro de `op.create_table`. Los tipos se crean una sola
# vez explícitamente al inicio del `upgrade()`.
ROL_USUARIO = postgresql.ENUM(
    "administrador_ti", "personal_tecnico", "docente", "estudiante",
    name="rol_usuario", create_type=False,
)
BANDA_FRECUENCIA = postgresql.ENUM(
    "2.4_GHz", "5_GHz", "dual", name="banda_frecuencia", create_type=False,
)
TIPO_FALLA = postgresql.ENUM(
    "sin_senal", "lentitud", "desconexion_intermitente", "otro",
    name="tipo_falla", create_type=False,
)
ESTADO_TICKET = postgresql.ENUM(
    "activo", "en_proceso", "resuelto", name="estado_ticket", create_type=False,
)
PRIORIDAD_TICKET = postgresql.ENUM(
    "alta", "media", "baja", name="prioridad_ticket", create_type=False,
)
TIPO_ALERTA = postgresql.ENUM(
    "saturacion_carga", "latencia_alta", "nodo_caido",
    name="tipo_alerta", create_type=False,
)
ESTADO_ALERTA = postgresql.ENUM(
    "activa", "atendida", "cerrada_auto", "escalada",
    name="estado_alerta", create_type=False,
)
TIPO_REPORTE = postgresql.ENUM(
    "sla_mensual", "disponibilidad_diaria", "incidencias",
    name="tipo_reporte", create_type=False,
)

_ENUM_DEFINITIONS: list[tuple[str, tuple[str, ...]]] = [
    ("rol_usuario", ROL_USUARIO.enums),
    ("banda_frecuencia", BANDA_FRECUENCIA.enums),
    ("tipo_falla", TIPO_FALLA.enums),
    ("estado_ticket", ESTADO_TICKET.enums),
    ("prioridad_ticket", PRIORIDAD_TICKET.enums),
    ("tipo_alerta", TIPO_ALERTA.enums),
    ("estado_alerta", ESTADO_ALERTA.enums),
    ("tipo_reporte", TIPO_REPORTE.enums),
]


def upgrade() -> None:
    # Extensiones (idempotentes; init.sql también las crea, pero esto cubre entornos limpios).
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.execute("CREATE EXTENSION IF NOT EXISTS citext")
    op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb")

    for name, values in _ENUM_DEFINITIONS:
        values_sql = ", ".join(f"'{v}'" for v in values)
        op.execute(f"CREATE TYPE {name} AS ENUM ({values_sql})")

    # --- usuarios -------------------------------------------------------
    op.create_table(
        "usuarios",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("correo", postgresql.CITEXT(), nullable=False, unique=True),
        sa.Column("nombre_completo", sa.String(200), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("rol", ROL_USUARIO, nullable=False),
        sa.Column("mfa_secret", sa.String(64), nullable=True),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
    )
    op.create_index("ix_usuarios_correo", "usuarios", ["correo"])
    op.create_index("ix_usuarios_rol", "usuarios", ["rol"])

    # --- edificios / pisos / aulas --------------------------------------
    op.create_table(
        "edificios",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("codigo", sa.String(20), nullable=False, unique=True),
        sa.Column("nombre", sa.String(150), nullable=False),
        sa.Column("descripcion", sa.String(500), nullable=True),
        sa.Column("latitud", sa.Float(), nullable=True),
        sa.Column("longitud", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
    )

    op.create_table(
        "pisos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("edificio_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("edificios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("numero", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(80), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.UniqueConstraint("edificio_id", "numero", name="piso_unico_por_edificio"),
    )
    op.create_index("ix_pisos_edificio_id", "pisos", ["edificio_id"])

    op.create_table(
        "aulas",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("piso_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("pisos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("codigo", sa.String(40), nullable=False),
        sa.Column("nombre", sa.String(150), nullable=True),
        sa.Column("tipo", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.UniqueConstraint("piso_id", "codigo", name="aula_unica_por_piso"),
    )
    op.create_index("ix_aulas_piso_id", "aulas", ["piso_id"])

    # --- access_points --------------------------------------------------
    op.create_table(
        "access_points",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("codigo", sa.String(40), nullable=False, unique=True),
        sa.Column("nombre", sa.String(100), nullable=False),
        sa.Column("modelo", sa.String(100), nullable=True),
        sa.Column("mac_address", sa.String(17), nullable=True, unique=True),
        sa.Column("aula_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("aulas.id", ondelete="SET NULL"), nullable=True),
        sa.Column("banda", BANDA_FRECUENCIA, nullable=False, server_default="dual"),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
    )
    op.create_index("ix_access_points_aula_id", "access_points", ["aula_id"])

    # --- alertas (antes que tickets por FK ticket→alerta) ---------------
    op.create_table(
        "alertas",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("access_point_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("access_points.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tipo", TIPO_ALERTA, nullable=False),
        sa.Column("estado", ESTADO_ALERTA, nullable=False, server_default="activa"),
        sa.Column("umbral_violado", sa.Float(), nullable=False),
        sa.Column("valor_observado", sa.Float(), nullable=False),
        sa.Column("detectada_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("atendida_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("atendida_por_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True),
        sa.Column("comentario_resolucion", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
    )
    op.create_index("ix_alertas_access_point_id", "alertas", ["access_point_id"])
    op.create_index("ix_alertas_estado", "alertas", ["estado"])
    op.create_index("ix_alertas_detectada_at", "alertas", ["detectada_at"])

    # --- tickets / ticket_historico -------------------------------------
    op.create_table(
        "tickets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("reportante_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("asignado_a_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True),
        sa.Column("edificio_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("edificios.id"), nullable=False),
        sa.Column("piso_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("pisos.id"), nullable=True),
        sa.Column("aula_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("aulas.id"), nullable=True),
        sa.Column("gps_cifrado", sa.LargeBinary(), nullable=True),
        sa.Column("geohash", sa.String(12), nullable=True),
        sa.Column("tipo_falla", TIPO_FALLA, nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("estado", ESTADO_TICKET, nullable=False, server_default="activo"),
        sa.Column("prioridad", PRIORIDAD_TICKET, nullable=False, server_default="media"),
        sa.Column("alerta_origen_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("alertas.id", ondelete="SET NULL"), nullable=True),
        sa.Column("cerrado_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
    )
    op.create_index("ix_tickets_reportante_id", "tickets", ["reportante_id"])
    op.create_index("ix_tickets_asignado_a_id", "tickets", ["asignado_a_id"])
    op.create_index("ix_tickets_estado", "tickets", ["estado"])
    op.create_index("ix_tickets_geohash", "tickets", ["geohash"])

    op.create_table(
        "ticket_historico",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("ticket_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("responsable_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True),
        sa.Column("estado_anterior", ESTADO_TICKET, nullable=True),
        sa.Column("estado_nuevo", ESTADO_TICKET, nullable=False),
        sa.Column("comentario", sa.Text(), nullable=True),
        sa.Column("fecha", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
    )
    op.create_index("ix_ticket_historico_ticket_id", "ticket_historico", ["ticket_id"])
    op.create_index("ix_ticket_historico_fecha", "ticket_historico", ["fecha"])

    # --- configuracion_umbrales -----------------------------------------
    op.create_table(
        "configuracion_umbrales",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("carga_pct", sa.Float(), nullable=False, server_default="80"),
        sa.Column("latencia_ms", sa.Float(), nullable=False, server_default="100"),
        sa.Column("duracion_minima_seg", sa.Integer(), nullable=False, server_default="120"),
        sa.Column("actualizado_por_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
    )

    # --- speedtest_resultados -------------------------------------------
    op.create_table(
        "speedtest_resultados",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("usuario_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("edificio_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("edificios.id", ondelete="SET NULL"), nullable=True),
        sa.Column("piso_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("pisos.id", ondelete="SET NULL"), nullable=True),
        sa.Column("aula_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("aulas.id", ondelete="SET NULL"), nullable=True),
        sa.Column("velocidad_bajada_mbps", sa.Float(), nullable=False),
        sa.Column("velocidad_subida_mbps", sa.Float(), nullable=False),
        sa.Column("latencia_ms", sa.Float(), nullable=False),
        sa.Column("ip_origen", sa.String(45), nullable=True),
        sa.Column("ejecutado_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
    )
    op.create_index(
        "ix_speedtest_resultados_usuario_id", "speedtest_resultados", ["usuario_id"]
    )
    op.create_index(
        "ix_speedtest_resultados_ejecutado_at", "speedtest_resultados", ["ejecutado_at"]
    )

    # --- reportes_sla ---------------------------------------------------
    op.create_table(
        "reportes_sla",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tipo", TIPO_REPORTE, nullable=False),
        sa.Column("rango_inicio", sa.DateTime(timezone=True), nullable=False),
        sa.Column("rango_fin", sa.DateTime(timezone=True), nullable=False),
        sa.Column("edificio_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("edificios.id", ondelete="SET NULL"), nullable=True),
        sa.Column("generado_por_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("pdf_url", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
    )

    # --- audit_log ------------------------------------------------------
    op.create_table(
        "audit_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("usuario_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True),
        sa.Column("accion", sa.String(100), nullable=False),
        sa.Column("entidad", sa.String(100), nullable=True),
        sa.Column("entidad_id", sa.String(64), nullable=True),
        sa.Column("datos", postgresql.JSONB(), nullable=True),
        sa.Column("ip_origen", postgresql.INET(), nullable=True),
        sa.Column("fecha", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
    )
    op.create_index("ix_audit_log_usuario_id", "audit_log", ["usuario_id"])
    op.create_index("ix_audit_log_accion", "audit_log", ["accion"])
    op.create_index("ix_audit_log_fecha", "audit_log", ["fecha"])

    # --- metricas_monitoreo (hypertable TimescaleDB) --------------------
    op.create_table(
        "metricas_monitoreo",
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("access_point_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("access_points.id", ondelete="CASCADE"), nullable=False),
        sa.Column("ancho_banda_mbps", sa.Float(), nullable=False),
        sa.Column("latencia_ms", sa.Float(), nullable=False),
        sa.Column("carga_pct", sa.Float(), nullable=False),
        sa.Column("paquetes_perdidos", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("clientes_conectados", sa.Integer(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("ts", "access_point_id", name="pk_metricas_monitoreo"),
    )
    op.create_index("ix_metricas_monitoreo_ts", "metricas_monitoreo", ["ts"])
    # Particiona por tiempo cada 7 días.
    op.execute(
        "SELECT create_hypertable('metricas_monitoreo', 'ts', "
        "chunk_time_interval => INTERVAL '7 days', if_not_exists => TRUE);"
    )


def downgrade() -> None:
    op.drop_table("metricas_monitoreo")
    op.drop_index("ix_audit_log_fecha", table_name="audit_log")
    op.drop_index("ix_audit_log_accion", table_name="audit_log")
    op.drop_index("ix_audit_log_usuario_id", table_name="audit_log")
    op.drop_table("audit_log")
    op.drop_table("reportes_sla")
    op.drop_index("ix_speedtest_resultados_ejecutado_at", table_name="speedtest_resultados")
    op.drop_index("ix_speedtest_resultados_usuario_id", table_name="speedtest_resultados")
    op.drop_table("speedtest_resultados")
    op.drop_table("configuracion_umbrales")
    op.drop_index("ix_ticket_historico_fecha", table_name="ticket_historico")
    op.drop_index("ix_ticket_historico_ticket_id", table_name="ticket_historico")
    op.drop_table("ticket_historico")
    op.drop_index("ix_tickets_geohash", table_name="tickets")
    op.drop_index("ix_tickets_estado", table_name="tickets")
    op.drop_index("ix_tickets_asignado_a_id", table_name="tickets")
    op.drop_index("ix_tickets_reportante_id", table_name="tickets")
    op.drop_table("tickets")
    op.drop_index("ix_alertas_detectada_at", table_name="alertas")
    op.drop_index("ix_alertas_estado", table_name="alertas")
    op.drop_index("ix_alertas_access_point_id", table_name="alertas")
    op.drop_table("alertas")
    op.drop_index("ix_access_points_aula_id", table_name="access_points")
    op.drop_table("access_points")
    op.drop_index("ix_aulas_piso_id", table_name="aulas")
    op.drop_table("aulas")
    op.drop_index("ix_pisos_edificio_id", table_name="pisos")
    op.drop_table("pisos")
    op.drop_table("edificios")
    op.drop_index("ix_usuarios_rol", table_name="usuarios")
    op.drop_index("ix_usuarios_correo", table_name="usuarios")
    op.drop_table("usuarios")

    for name, _ in reversed(_ENUM_DEFINITIONS):
        op.execute(f"DROP TYPE IF EXISTS {name}")

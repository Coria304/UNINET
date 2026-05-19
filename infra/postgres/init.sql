-- UniNet Connect — Inicialización de PostgreSQL
-- Se ejecuta una sola vez cuando el volumen de Postgres está vacío.

-- Extensión TimescaleDB: requerida para `metricas_monitoreo` (RF002).
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- pgcrypto: requerida para anonimización de coordenadas GPS (RNF008).
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- citext: para correos institucionales case-insensitive (RF009).
CREATE EXTENSION IF NOT EXISTS citext;

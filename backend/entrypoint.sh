#!/bin/sh
set -e

echo "Corriendo migraciones..."
alembic upgrade head

echo "Cargando datos iniciales..."
python -m seeds.seed_escom

echo "Iniciando servidor..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"

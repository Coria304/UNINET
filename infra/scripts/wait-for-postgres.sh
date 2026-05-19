#!/usr/bin/env bash
# Espera hasta que Postgres acepte conexiones.
set -euo pipefail

host="${POSTGRES_HOST:-postgres}"
port="${POSTGRES_PORT:-5432}"
user="${POSTGRES_USER:-uninet}"

until pg_isready -h "$host" -p "$port" -U "$user" >/dev/null 2>&1; do
  echo "Esperando a postgres en ${host}:${port}..."
  sleep 1
done

echo "Postgres listo."

#!/usr/bin/env bash
# start.sh — Arranca toda la app UniNet Connect:
#   1. Levanta postgres + redis en contenedores (podman-compose / docker compose)
#   2. Crea backend/.venv e instala deps si faltan
#   3. Instala node_modules del frontend si faltan
#   4. Aplica migraciones Alembic
#   5. Si la BD está vacía: carga seed inicial (4 usuarios demo + ESCOM)
#   6. Arranca el backend (uvicorn :8000) en background
#   7. Arranca el frontend (vite :5173) en background
# Idempotente: si algo ya está corriendo, avisa y sale sin tocarlo.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_DIR="$REPO_ROOT/.run"
LOGS_DIR="$RUN_DIR/logs"
BACKEND_PID="$RUN_DIR/backend.pid"
FRONTEND_PID="$RUN_DIR/frontend.pid"
VENV="$REPO_ROOT/backend/.venv"

mkdir -p "$LOGS_DIR"

# --- Colores y logging ---
if [ -t 1 ]; then
    G=$'\033[0;32m'; Y=$'\033[0;33m'; R=$'\033[0;31m'; B=$'\033[0;34m'; N=$'\033[0m'; D=$'\033[1m'
else
    G='' Y='' R='' B='' N='' D=''
fi
ok()   { printf '  %b✓%b %s\n' "$G" "$N" "$*"; }
info() { printf '  %b▸%b %s\n' "$B" "$N" "$*"; }
warn() { printf '  %b!%b %s\n' "$Y" "$N" "$*"; }
die()  { printf '  %b✗%b %s\n' "$R" "$N" "$*" >&2; exit 1; }

printf '\n%b== UniNet Connect: start ==%b\n\n' "$D" "$N"

# --- 1. Detectar compose ---
if command -v podman-compose >/dev/null 2>&1; then
    COMPOSE=podman-compose
elif docker compose version >/dev/null 2>&1; then
    COMPOSE="docker compose"
else
    die "Necesitas podman-compose o docker compose. Instala con: sudo dnf install podman-compose"
fi

# --- 1b. Cargar .env raíz y componer URLs para ejecución local ---
# El docker-compose.yml compone DATABASE_URL/REDIS_URL/SECRET_KEY internamente
# para el contenedor backend. Aquí los recomponemos apuntando a localhost,
# porque uvicorn/alembic correrán fuera del contenedor (en el venv).
if [ -f "$REPO_ROOT/.env" ]; then
    set -a
    # shellcheck disable=SC1091
    source "$REPO_ROOT/.env"
    set +a
else
    warn ".env no encontrado en la raíz; usaré valores por defecto."
fi
export DATABASE_URL="postgresql+psycopg://${POSTGRES_USER:-uninet}:${POSTGRES_PASSWORD:-uninet_dev}@localhost:${POSTGRES_PORT:-5432}/${POSTGRES_DB:-uninet}"
export REDIS_URL="redis://localhost:${REDIS_PORT:-6379}/0"
export SECRET_KEY="${SECRET_KEY:-dev-secret-change-in-prod-min-16}"
export ENVIRONMENT="${ENVIRONMENT:-development}"
# CORS_ORIGINS es list[str] en pydantic-settings: cuando viene de env intenta
# json.loads y falla con un valor plano. Se pasa como JSON o se deja el default
# ("http://localhost:5173"), que es exactamente lo que queremos en dev.
if [ -n "${CORS_ORIGINS:-}" ]; then
    case "$CORS_ORIGINS" in
        \[*\]) export CORS_ORIGINS ;;  # ya es JSON
        *)     unset CORS_ORIGINS ;;   # plano → usar el default de Settings
    esac
fi

# Vite lee .env desde frontend/. Si no existe, lo creamos a partir del ejemplo.
if [ ! -f "$REPO_ROOT/frontend/.env" ] && [ -f "$REPO_ROOT/frontend/.env.example" ]; then
    cp "$REPO_ROOT/frontend/.env.example" "$REPO_ROOT/frontend/.env"
    info "Creado frontend/.env desde .env.example"
fi

# --- 2. Verificar que no haya un arranque previo activo ---
already_running() {
    local pidfile="$1"
    [ -f "$pidfile" ] && kill -0 "$(cat "$pidfile" 2>/dev/null)" 2>/dev/null
}
if already_running "$BACKEND_PID"; then
    die "Backend ya corre (PID $(cat "$BACKEND_PID")). Ejecuta ./stop.sh primero."
fi
if already_running "$FRONTEND_PID"; then
    die "Frontend ya corre (PID $(cat "$FRONTEND_PID")). Ejecuta ./stop.sh primero."
fi
rm -f "$BACKEND_PID" "$FRONTEND_PID"

# --- 3. Bootstrap venv si falta ---
if [ ! -x "$VENV/bin/python" ]; then
    info "Creando venv Python 3.12 (primera vez)..."
    command -v python3.12 >/dev/null 2>&1 || die "python3.12 no encontrado. Instala con: sudo dnf install python3.12"
    python3.12 -m venv "$VENV"
    "$VENV/bin/pip" install --upgrade pip setuptools wheel >/dev/null
    "$VENV/bin/pip" install -r "$REPO_ROOT/backend/requirements-dev.txt"
    ok "Venv y dependencias backend instaladas."
fi

# --- 4. Bootstrap frontend si falta ---
if [ ! -d "$REPO_ROOT/frontend/node_modules" ]; then
    info "Instalando dependencias frontend (primera vez)..."
    command -v npm >/dev/null 2>&1 || die "npm no encontrado. Instala Node 20+."
    (cd "$REPO_ROOT/frontend" && npm install)
    ok "Dependencias frontend instaladas."
fi

# --- 5. Arrancar postgres + redis ---
info "Arrancando postgres + redis..."
(cd "$REPO_ROOT" && $COMPOSE up -d postgres redis >/dev/null)
info "Esperando a postgres..."
for _ in $(seq 1 30); do
    if (cd "$REPO_ROOT" && $COMPOSE exec -T postgres pg_isready -U "${POSTGRES_USER:-uninet}" >/dev/null 2>&1); then
        ok "postgres listo."
        break
    fi
    sleep 1
done

# --- 6. Aplicar migraciones ---
info "Aplicando migraciones Alembic..."
(cd "$REPO_ROOT/backend" && "$VENV/bin/alembic" upgrade head >"$LOGS_DIR/migrate.log" 2>&1) \
    || die "Migración falló. Revisa .run/logs/migrate.log"
ok "Migraciones aplicadas."

# --- 6b. Cargar seed sólo si la BD está vacía (idempotente) ---
# Cuentas demo: admin.ti / tecnico1 / docente1 / estudiante1 @escom.ipn.mx
user_count="$(cd "$REPO_ROOT/backend" && "$VENV/bin/python" -c "
from sqlalchemy import func, select
from app.core.database import SessionLocal
from app.models import Usuario
with SessionLocal() as s:
    print(s.scalar(select(func.count(Usuario.id))) or 0)
" 2>/dev/null || echo "0")"
if [ "$user_count" = "0" ]; then
    info "BD vacía → cargando seed inicial (usuarios demo + ESCOM)..."
    (cd "$REPO_ROOT/backend" && "$VENV/bin/python" -m seeds.seed_escom >"$LOGS_DIR/seed.log" 2>&1) \
        || die "Seed falló. Revisa .run/logs/seed.log"
    ok "Seed cargado. Cuentas demo disponibles (ver .run/logs/seed.log)."
fi

# --- 7. Arrancar backend ---
info "Arrancando backend (uvicorn :8000)..."
(
    cd "$REPO_ROOT/backend"
    # setsid + nohup: nuevo process group y supervivencia al cierre de la terminal.
    setsid nohup "$VENV/bin/python" -m uvicorn app.main:app --reload \
        --host 0.0.0.0 --port 8000 \
        >"$LOGS_DIR/backend.log" 2>&1 &
    echo $! > "$BACKEND_PID"
)
sleep 2
if ! kill -0 "$(cat "$BACKEND_PID")" 2>/dev/null; then
    rm -f "$BACKEND_PID"
    die "Backend murió en el arranque. Revisa .run/logs/backend.log"
fi
for _ in $(seq 1 30); do
    if curl -fs http://localhost:8000/api/v1/health >/dev/null 2>&1; then
        ok "backend listo en http://localhost:8000"
        break
    fi
    sleep 1
done

# --- 8. Arrancar frontend ---
info "Arrancando frontend (vite :5173)..."
(
    cd "$REPO_ROOT/frontend"
    setsid nohup npm run dev -- --host 0.0.0.0 \
        >"$LOGS_DIR/frontend.log" 2>&1 &
    echo $! > "$FRONTEND_PID"
)
sleep 2
if ! kill -0 "$(cat "$FRONTEND_PID")" 2>/dev/null; then
    rm -f "$FRONTEND_PID"
    die "Frontend murió en el arranque. Revisa .run/logs/frontend.log"
fi
for _ in $(seq 1 30); do
    if curl -fs http://localhost:5173 >/dev/null 2>&1; then
        ok "frontend listo en http://localhost:5173"
        break
    fi
    sleep 1
done

printf '\n%b== Listo ==%b\n' "$D" "$N"
echo "  Backend:  http://localhost:8000   (Swagger en /docs)"
echo "  Frontend: http://localhost:5173"
echo
printf '  %bCuentas demo%b (todas @escom.ipn.mx):\n' "$D" "$N"
echo "    admin.ti      / admin1234       (ADMINISTRADOR_TI, requiere MFA)"
echo "    tecnico1      / tecnico1234     (PERSONAL_TECNICO)"
echo "    docente1      / docente1234     (DOCENTE)"
echo "    estudiante1   / alumno1234      (ESTUDIANTE)"
echo
echo "  Logs:  tail -f .run/logs/backend.log .run/logs/frontend.log"
echo "  Stop:  ./stop.sh"
echo

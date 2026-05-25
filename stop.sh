#!/usr/bin/env bash
# stop.sh — Detiene todo lo que arrancó start.sh:
#   - frontend (vite) y backend (uvicorn) por PID file
#   - cualquier uvicorn/vite huérfano (por si se borró el PID a mano)
#   - postgres + redis (sin borrar volúmenes)
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_DIR="$REPO_ROOT/.run"
BACKEND_PID="$RUN_DIR/backend.pid"
FRONTEND_PID="$RUN_DIR/frontend.pid"

if [ -t 1 ]; then
    G=$'\033[0;32m'; Y=$'\033[0;33m'; B=$'\033[0;34m'; N=$'\033[0m'; D=$'\033[1m'
else
    G='' Y='' B='' N='' D=''
fi
ok()   { printf '  %b✓%b %s\n' "$G" "$N" "$*"; }
info() { printf '  %b▸%b %s\n' "$B" "$N" "$*"; }
warn() { printf '  %b!%b %s\n' "$Y" "$N" "$*"; }

printf '\n%b== UniNet Connect: stop ==%b\n\n' "$D" "$N"

if command -v podman-compose >/dev/null 2>&1; then
    COMPOSE=podman-compose
elif docker compose version >/dev/null 2>&1; then
    COMPOSE="docker compose"
else
    COMPOSE=""
fi

stop_process() {
    local label="$1" pidfile="$2"
    if [ ! -f "$pidfile" ]; then
        warn "$label: sin PID file."
        return
    fi
    local pid
    pid="$(cat "$pidfile" 2>/dev/null || true)"
    if [ -z "$pid" ] || ! kill -0 "$pid" 2>/dev/null; then
        warn "$label: PID $pid ya no existe."
        rm -f "$pidfile"
        return
    fi
    info "Deteniendo $label (PID $pid)..."
    # Mata el process group (creado con setsid en start.sh) → se lleva hijos también.
    kill -TERM "-$pid" 2>/dev/null || kill -TERM "$pid" 2>/dev/null || true
    for _ in 1 2 3 4 5; do
        kill -0 "$pid" 2>/dev/null || break
        sleep 1
    done
    if kill -0 "$pid" 2>/dev/null; then
        warn "$label no respondió a SIGTERM, mandando SIGKILL."
        kill -KILL "-$pid" 2>/dev/null || kill -KILL "$pid" 2>/dev/null || true
    fi
    rm -f "$pidfile"
    ok "$label detenido."
}

stop_process "frontend" "$FRONTEND_PID"
stop_process "backend"  "$BACKEND_PID"

# Best-effort: matar procesos huérfanos si el PID file fue borrado a mano.
# Los patrones son específicos (rutas de venv/node_modules) para no matar
# shells o editores que casualmente tengan "vite" o "uvicorn" en su cmdline.
if pkill -f "$REPO_ROOT/backend/\.venv/bin/python.*uvicorn" 2>/dev/null; then
    ok "uvicorn huérfano detenido."
fi
if pkill -f "$REPO_ROOT/frontend/node_modules/vite" 2>/dev/null; then
    ok "vite huérfano detenido."
fi

if [ -n "$COMPOSE" ]; then
    info "Deteniendo postgres + redis (volúmenes intactos)..."
    (cd "$REPO_ROOT" && $COMPOSE stop postgres redis >/dev/null 2>&1) || true
    ok "Contenedores detenidos."
fi

printf '\n%b== Todo detenido ==%b\n\n' "$D" "$N"

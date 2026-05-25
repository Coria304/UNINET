# UniNet Connect

Plataforma web de monitoreo y gestión de red Wi-Fi en tiempo real para campus universitarios (ESCOM-IPN).

**Stack:** React 18 + TypeScript + Vite · FastAPI + SQLAlchemy + Alembic · PostgreSQL 16 con TimescaleDB · Redis · Docker Compose.

## Estructura del monorepo

```
UNINET/
├── backend/                FastAPI (capas: api → services → repositories → models)
├── frontend/               React + TypeScript + Vite
├── infra/                  Scripts y configuración de infraestructura
│   ├── postgres/init.sql   Habilita extensiones timescaledb y pgcrypto
│   └── scripts/            Utilidades de desarrollo
├── docs/                   Documentación técnica y de arquitectura
├── .github/workflows/      Pipelines CI (lint, test, build)
├── docker-compose.yml      Pila local de desarrollo
├── .env.example            Variables compartidas
├── start.sh                Arranca toda la app (DB + backend + frontend)
└── stop.sh                 Detiene todo
```

## Requisitos previos

- Podman 5+ con `podman-compose` (o Docker 24+ con Docker Compose v2)
- Python 3.12 y Node 20+

## Puesta en marcha

```bash
cp .env.example .env
./start.sh                # levanta DB, backend (uvicorn) y frontend (vite)
```

La primera vez crea el venv, instala dependencias backend + frontend y aplica migraciones. Las siguientes corridas son casi instantáneas.

Servicios disponibles:

- Backend (API + docs Swagger): http://localhost:8000/docs
- Frontend (Vite dev): http://localhost:5173
- PostgreSQL: localhost:5432 (user `uninet` / db `uninet`)
- Redis: localhost:6379

## Detener todo

```bash
./stop.sh                 # mata backend + frontend y detiene contenedores
```

Logs en vivo mientras corre:

```bash
tail -f .run/logs/backend.log .run/logs/frontend.log
```

Para usar Docker en vez de Podman:

```bash
COMPOSE="docker compose" ./start.sh
```

## Estado de Sprint 0 (preparación)

- [x] Estructura del monorepo
- [x] Docker Compose (postgres + timescale, redis, backend, frontend)
- [x] Esqueleto FastAPI por capas
- [x] Esqueleto React con rutas protegidas por rol y cliente HTTP con JWT
- [x] Migración Alembic inicial con todas las entidades
- [x] Seed de ESCOM
- [x] CI básico (lint + test + build)

Próximo: **Sprint 1 — Autenticación (RF009) y CU-10**.

## Equipo

| Integrante | Rol |
|---|---|
| Chavez Barrera Erick Azael | Project Manager |
| Hernández Bernal Luis Adrián | Desarrollador Full Stack |
| López Coria Axel Yahir | Analista de Sistemas |
| Tecuapacho German Iván | Documentador / Apoyo Técnico |
| Mejia Mejia Mauricio Xavier | Diseñador UI/UX |
| Romero Contreras Eber Ismael | QA Engineer |

ESCOM-IPN · Grupo 5CM1 · Formulación y Evaluación de Proyectos Informáticos.

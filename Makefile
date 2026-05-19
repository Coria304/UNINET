# UniNet Connect — Atajos de desarrollo
# Uso: `make <objetivo>`. Ver `make help` para la lista.

SHELL := /bin/bash
COMPOSE := docker compose

.DEFAULT_GOAL := help

help: ## Lista los objetivos disponibles
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

up: ## Levanta toda la pila (postgres, redis, backend, frontend)
	$(COMPOSE) up -d

down: ## Detiene la pila
	$(COMPOSE) down

logs: ## Sigue los logs de todos los servicios
	$(COMPOSE) logs -f

ps: ## Muestra el estado de los servicios
	$(COMPOSE) ps

build: ## Reconstruye las imágenes
	$(COMPOSE) build

migrate: ## Aplica las migraciones Alembic
	$(COMPOSE) exec backend alembic upgrade head

migration: ## Genera una nueva revisión Alembic (uso: make migration m="mensaje")
	$(COMPOSE) exec backend alembic revision --autogenerate -m "$(m)"

seed: ## Pobla la base de datos con el seed inicial de ESCOM
	$(COMPOSE) exec backend python -m seeds.seed_escom

reset-db: ## Recrea la base de datos desde cero (DESTRUCTIVO)
	$(COMPOSE) down -v
	$(COMPOSE) up -d postgres redis
	@sleep 3
	$(COMPOSE) up -d backend
	@sleep 3
	$(MAKE) migrate
	$(MAKE) seed

test-backend: ## Ejecuta la suite de pytest del backend
	$(COMPOSE) exec backend pytest

test-frontend: ## Ejecuta la suite de Vitest del frontend
	$(COMPOSE) exec frontend npm test

lint-backend: ## Lint del backend (ruff)
	$(COMPOSE) exec backend ruff check app tests

lint-frontend: ## Lint del frontend (eslint)
	$(COMPOSE) exec frontend npm run lint

shell-backend: ## Abre una shell en el contenedor backend
	$(COMPOSE) exec backend bash

shell-db: ## Abre psql contra la base de datos
	$(COMPOSE) exec postgres psql -U $${POSTGRES_USER:-uninet} -d $${POSTGRES_DB:-uninet}

.PHONY: help up down logs ps build migrate migration seed reset-db test-backend test-frontend lint-backend lint-frontend shell-backend shell-db

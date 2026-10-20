# Atalhos do Flowo. Tudo roda dentro dos containers, então só é preciso Docker.
# Compatível com GNU Make no Windows (cmd ou sh): use apenas aspas duplas.

# Lê as sobrescritas opcionais do .env (mesmas variáveis usadas pelo docker-compose.yml).
-include .env
POSTGRES_USER ?= flowo
POSTGRES_DB ?= flowo

COMPOSE  := docker compose
# `--build` reconstrói a imagem se as dependências mudaram (ex.: depois de um git pull).
BACKEND  := $(COMPOSE) run --rm --build backend
BACKEND_NODB := $(COMPOSE) run --rm --build --no-deps backend
FRONTEND := $(COMPOSE) run --rm --build --no-deps frontend

.DEFAULT_GOAL := help
.PHONY: help dev up down logs build test test-backend test-frontend lint lint-backend \
	lint-frontend format types migrate migration seed psql

# Impresso pelo próprio make ($(info)), igual no cmd.exe e no sh.
define HELP
Flowo - comandos disponiveis:
  make dev            sobe db, backend e frontend com hot reload
  make up             sobe tudo em segundo plano
  make down           derruba os containers
  make logs           acompanha os logs
  make test           roda pytest e Vitest
  make lint           Ruff + mypy + ESLint + Prettier + tsc
  make format         formata backend e frontend
  make types          exporta o JSON Schema e gera os tipos TypeScript
  make migrate        aplica as migracoes Alembic
  make migration name=descricao   cria uma migracao (autogenerate)
  make seed           cria um workflow de exemplo
  make psql           abre o psql no banco de desenvolvimento
endef

help:
	$(info $(HELP))
	@exit 0

dev:
	$(COMPOSE) up --build --renew-anon-volumes

up:
	$(COMPOSE) up --build --renew-anon-volumes --detach

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs --follow

build:
	$(COMPOSE) build

test: test-backend test-frontend

test-backend:
	$(BACKEND) uv run pytest

test-frontend:
	$(FRONTEND) npm test

lint: lint-backend lint-frontend

lint-backend:
	$(BACKEND_NODB) sh -c "uv run ruff check . && uv run ruff format --check . && uv run mypy ."

lint-frontend:
	$(FRONTEND) npm run lint

format:
	$(BACKEND_NODB) sh -c "uv run ruff check --fix . && uv run ruff format ."
	$(FRONTEND) npm run format

types:
	$(BACKEND_NODB) uv run python -m scripts.export_schema
	$(FRONTEND) npm run gen:types

migrate:
	$(BACKEND) uv run alembic upgrade head

migration:
	$(if $(name),,$(error informe a descricao: make migration name=descricao))
	$(BACKEND) uv run alembic revision --autogenerate -m "$(name)"

seed:
	$(BACKEND) uv run python -m scripts.seed

psql:
	$(COMPOSE) exec db psql -U $(POSTGRES_USER) -d $(POSTGRES_DB)

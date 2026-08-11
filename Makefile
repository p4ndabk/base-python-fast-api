.PHONY: help install run test lint fmt up down logs migrate revision psql check

help:  ## Lista os comandos disponiveis
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

install:  ## Instala as dependencias (dev incluso)
	uv sync

run:  ## Sobe a API local com hot-reload
	uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:  ## Roda a suite de testes
	uv run pytest -v

lint:  ## Verifica lint e formatacao
	uv run ruff check .
	uv run ruff format --check .

fmt:  ## Formata o codigo e corrige o que for automatico
	uv run ruff format .
	uv run ruff check --fix .

check: lint test  ## Lint + testes (rode antes de abrir PR)

up:  ## Sobe api + banco no docker
	docker compose up -d --build

down:  ## Derruba os containers
	docker compose down

logs:  ## Acompanha os logs da api
	docker compose logs -f api

migrate:  ## Aplica as migrations pendentes
	uv run alembic upgrade head

revision:  ## Gera uma migration nova: make revision m="cria tabela products"
	uv run alembic revision --autogenerate -m "$(m)"

psql:  ## Abre o psql no banco do compose
	docker compose exec db psql -U postgres -d app

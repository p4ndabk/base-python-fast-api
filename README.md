# base-python-fast-api

Template base de API em FastAPI com arquitetura em camadas (DDD pragmático),
pensado para que qualquer pessoa — ou qualquer IA — consiga adicionar um módulo
novo seguindo um caminho único e explícito.

**Stack:** Python 3.11 · FastAPI · SQLAlchemy 2.0 async · PostgreSQL · Alembic · uv · pytest · Docker

## Começando

```bash
cp .env.example .env
uv sync                             # instala as dependencias
docker compose up -d --build        # api + postgres
uv run alembic upgrade head         # aplica as migrations
```

Ou rodando a API local, com só o Postgres no docker:

```bash
docker compose up -d db
uv run alembic upgrade head
uv run uvicorn app.main:app --reload   # http://localhost:8000/docs
```

## Arquitetura

```
HTTP → router.py → controller.py → service.py → repository.py → models.py
                                        ↕
                                   schemas.py
```

Cada camada só chama a camada imediatamente abaixo:

| Arquivo | Responsabilidade |
|---|---|
| `router.py` | path, método, status code, `response_model`, dependências |
| `controller.py` | orquestra e converte model → schema de saída |
| `service.py` | regra de negócio, validações, transação |
| `repository.py` | único lugar com query SQL |
| `models.py` | mapeamento de tabela |
| `schemas.py` | contratos de entrada/saída |

## Estrutura

```
app/
├── core/       config, exceptions, security, logging, schemas compartilhados
├── database/   Base declarativa e sessão async
├── api/        deps.py (dependências transversais), v1.py (agregador)
└── modules/
    ├── health/ liveness + readiness (verifica o banco de verdade)
    ├── users/  CRUD completo — módulo de referência
    └── auth/   register, login, refresh, /me (JWT)
AGENTS.md       como escrever o código (leitura obrigatória)
.rules/         regras de negócio versionadas (RN-*)
.claude/        base_spec.md e uma skill por camada (regra + exemplo + template)
alembic/        migrations
tests/          pytest async com httpx
```

## Documentação para quem for desenvolver (humano ou IA)

| Documento | Responde |
|---|---|
| [`AGENTS.md`](AGENTS.md) | **comece por aqui** — como escrever o código: camadas, convenções, anti-padrões, onde ficam os templates |
| [`CLAUDE.md`](CLAUDE.md) | ponteiro curto para o `AGENTS.md` |
| [`.claude/base_spec.md`](.claude/base_spec.md) | o rito obrigatório para criar uma rota |
| [`.rules/`](.rules/README.md) | **o que** o sistema deve fazer: as regras de negócio |
| `.claude/skills/<camada>/` | regra + exemplo + template de cada camada |

Cada regra de negócio tem um ID (`RN-USERS-002`) citado no service e no teste que
a implementam — `grep -r RN-USERS-002 .` mostra os três.

## Endpoints

| Método | Rota | Auth | Descrição |
|---|---|---|---|
| GET | `/health/live` | — | liveness (não toca no banco) |
| GET | `/health/ready` | — | readiness (503 se o banco estiver fora) |
| POST | `/auth/register` | — | cria a conta |
| POST | `/auth/login` | — | access + refresh token |
| POST | `/auth/refresh` | — | renova os tokens |
| GET | `/auth/me` | ✓ | usuário autenticado |
| POST | `/users` | — | cria usuário |
| GET | `/users` | ✓ | lista paginada |
| GET | `/users/{id}` | ✓ | busca por id |
| PATCH | `/users/{id}` | ✓ | atualização parcial |
| DELETE | `/users/{id}` | ✓ | remove |

## Comandos

Todo comando roda por `uv` — sem Makefile, sem script wrapper.

```bash
uv sync                                   # instala dependencias
uv add <pacote>                           # adiciona uma lib (--dev para dev)

uv run uvicorn app.main:app --reload      # API local com hot-reload
uv run pytest                             # testes
uv run ruff check .                       # lint
uv run ruff format .                      # formata

uv run alembic upgrade head                            # aplica migrations
uv run alembic revision --autogenerate -m "descricao"  # gera migration

docker compose up -d --build              # api + postgres
docker compose down
docker compose exec db psql -U postgres -d app
```

Antes de abrir PR: `uv run ruff check . && uv run pytest`

## Criando um módulo novo

Siga [`.claude/skills/new-module/SKILL.md`](.claude/skills/new-module/SKILL.md).
Resumo:

```
formulário (base_spec.md) → .rules/ → schemas → models → repository → service
  → controller → router → api/v1.py → alembic/env.py → migration → testes → ruff + pytest
```

Os testes rodam em SQLite em memória por padrão; para usar Postgres:
`TEST_DATABASE_URL=postgresql+asyncpg://... uv run pytest`.

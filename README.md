# base-python-fast-api

Template base de API em FastAPI com arquitetura em camadas (DDD pragmático),
pensado para que qualquer pessoa — ou qualquer IA — consiga adicionar um módulo
novo seguindo um caminho único e explícito.

**Stack:** Python 3.11 · FastAPI · SQLAlchemy 2.0 async · PostgreSQL · Alembic · uv · pytest · Docker

## Começando

```bash
cp .env.example .env
make install          # uv sync
make up               # sobe api + postgres no docker
make migrate          # aplica as migrations
```

Ou local, com o Postgres do compose:

```bash
docker compose up -d db
make migrate
make run              # http://localhost:8000/docs
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

```bash
make help       # lista tudo
make run        # API local com hot-reload
make test       # pytest
make lint       # ruff check + format --check
make check      # lint + test (rode antes do PR)
make up / down  # docker compose
make migrate    # alembic upgrade head
make revision m="cria tabela products"
```

## Criando um módulo novo

Siga [`.claude/skills/new-module/SKILL.md`](.claude/skills/new-module/SKILL.md).
Resumo:

```
formulário (base_spec.md) → .rules/ → schemas → models → repository → service
  → controller → router → api/v1.py → alembic/env.py → migration → testes → make check
```

Os testes rodam em SQLite em memória por padrão; para usar Postgres:
`TEST_DATABASE_URL=postgresql+asyncpg://... uv run pytest`.

# Base FastAPI + DDD pragmático (async SQLAlchemy 2.0 + PostgreSQL)

## Context

O repositório está vazio (apenas `README.md` e git). O objetivo é criar um **template base reutilizável** de API em FastAPI com arquitetura em camadas (DDD pragmático), organizado de forma tão explícita e repetitiva que **qualquer IA, mesmo modelos fracos, consiga adicionar um módulo novo sem inventar padrões**.

O produto final tem duas partes inseparáveis:
1. **O código** — um projeto funcional com auth JWT, migrations e Docker.
2. **A documentação executável em `.claude/`** — `CLAUDE.md` curto no root apontando para `.claude/AGENTS.md` (regras duras), uma skill `new-module` (passo a passo determinístico) e `.claude/templates/` com arquivos-modelo copiáveis.

Decisões já confirmadas: async + PostgreSQL; auth JWT + usuários; Docker Compose; Alembic; 4 camadas pragmáticas.

## Ferramentas fixas

- **Gerenciador de dependências: `uv`** (já instalado em `/opt/homebrew/bin/uv`). `pyproject.toml` + `uv.lock` versionados; sem `requirements.txt`, sem `pip install` avulso. Todo comando roda via `uv run ...` — inclusive dentro do Dockerfile e do Makefile — e novas libs entram com `uv add` / `uv add --dev`.
- **Testes: `pytest`** + `pytest-asyncio` (`asyncio_mode = "auto"`) + `httpx.AsyncClient`. Sem `unittest`. `uv run pytest` é o único comando de teste, e `AGENTS.md` exige que todo módulo novo venha com testes passando.

## Arquitetura — regra única de dependência

```
HTTP → router.py → controller.py → service.py → repository.py → models.py (SQLAlchemy)
                                        ↕
                                   schemas.py (Pydantic)
```

Regra que a IA nunca pode quebrar: **cada camada só chama a camada imediatamente abaixo**.

| Arquivo | Responsabilidade | Pode importar | NUNCA faz |
|---|---|---|---|
| `router.py` | paths, status codes, `response_model`, deps | controller, schemas | lógica, SQLAlchemy |
| `controller.py` | orquestra, traduz erros de domínio → HTTPException | service, schemas | query SQL |
| `service.py` | regra de negócio, validações, transação | repository, schemas, exceptions | `HTTPException`, `Request` |
| `repository.py` | único lugar com `select()/session` | models, `AsyncSession` | regra de negócio |
| `models.py` | tabelas (`Mapped`/`mapped_column`) | `database.base` | Pydantic |
| `schemas.py` | contratos de entrada/saída | — | SQLAlchemy |

Erros de domínio (`NotFoundError`, `ConflictError`, `ValidationError`) vivem em `app/core/exceptions.py`, são lançados no service e convertidos em HTTP por exception handlers globais em `main.py` (o controller não precisa try/except na maioria dos casos).

## Estrutura de arquivos a criar

```
.
├── CLAUDE.md                        # curto: "leia .claude/AGENTS.md antes de qualquer código"
├── pyproject.toml                   # uv, deps, config ruff/pytest
├── .env.example  .gitignore  .dockerignore
├── Dockerfile  docker-compose.yml   # api + postgres + healthcheck
├── Makefile                         # up, down, test, migrate, revision, lint, run
├── alembic.ini
├── alembic/{env.py, versions/}      # env.py async, autogenerate via Base.metadata
├── .claude/
│   ├── AGENTS.md                    # ★ regras, tabela de camadas, checklist, anti-padrões
│   ├── base_spec.md                 # ★ especificação normativa: como criar uma rota nova
│   ├── settings.json                # permissões p/ uv/pytest/alembic/docker
│   ├── skills/new-module/SKILL.md   # receita passo a passo p/ criar módulo
│   ├── examples/                    # ★ uma pasta por camada, exemplo real comentado
│   │   ├── README.md                #   índice: "quero fazer X → abra a pasta Y"
│   │   ├── 01-model/    {example_model.py, README.md}
│   │   ├── 02-schema/   {example_schemas.py, README.md}
│   │   ├── 03-repository/ {example_repository.py, README.md}
│   │   ├── 04-service/  {example_service.py, README.md}
│   │   ├── 05-controller/ {example_controller.py, README.md}
│   │   ├── 06-router/   {example_router.py, README.md}
│   │   ├── 07-tests/    {test_example_api.py, test_example_service.py, README.md}
│   │   └── 08-migration/ {example_migration.py, README.md}
│   └── templates/module/            # os mesmos arquivos, com {{Entity}} p/ copiar e colar
│       └── tests/
├── app/
│   ├── main.py                      # create_app(), lifespan, handlers, /health
│   ├── core/{config.py, security.py, exceptions.py, logging.py}
│   ├── database/{base.py, session.py}
│   ├── api/{deps.py, v1.py}         # get_db, get_current_user; v1.py agrega routers
│   └── modules/
│       ├── health/   # liveness + readiness (checa o banco)
│       ├── users/    # módulo de referência COMPLETO (CRUD + testes)
│       └── auth/     # register, login, refresh, /me
└── tests/{conftest.py, ...}         # httpx AsyncClient + Postgres de teste, rollback por teste
```

## Passos de implementação

### 0. Salvar o plano e PARAR (primeira e única ação inicial)
Copiar este documento para `PLAN.md` na raiz do projeto e **encerrar o turno ali**, sem criar nenhum outro arquivo. O usuário vai revisar o plano com calma e dará o aval para seguir. Os passos 1–8 só começam depois desse novo "ok" explícito.

### 1. Fundação
- `uv init` + `pyproject.toml` (`requires-python = ">=3.11"`), deps: `fastapi`, `uvicorn[standard]`, `sqlalchemy[asyncio]>=2.0`, `asyncpg`, `alembic`, `pydantic-settings`, `python-jose[cryptography]`, `passlib[argon2]`; dev: `pytest`, `pytest-asyncio`, `httpx`, `ruff`. Configuração `[tool.ruff]` e `[tool.pytest.ini_options]` (`asyncio_mode = "auto"`) inclusas — assumo que lint local é desejável mesmo sem CI.
- `app/core/config.py`: `Settings(BaseSettings)` com `DATABASE_URL`, `JWT_SECRET`, `JWT_ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `ENVIRONMENT`; instância única `settings`.
- `app/database/base.py`: `class Base(DeclarativeBase)` + mixin `TimestampMixin` (`id: UUID`, `created_at`, `updated_at`) que todo model herda.
- `app/database/session.py`: `create_async_engine`, `async_sessionmaker(expire_on_commit=False)`, generator `get_session()`.
- `app/core/exceptions.py`: `AppError` base + `NotFoundError`, `ConflictError`, `UnauthorizedError`, `DomainValidationError`.
- `app/main.py`: `create_app()`, registro dos handlers `AppError → JSONResponse`, CORS, inclusão de `app/api/v1.py`.

### 2. Módulo `health` (menor exemplo das camadas)
Módulo enxuto que serve de "hello world" da arquitetura — só `router.py`, `controller.py`, `service.py`, `repository.py`, `schemas.py` (sem `models.py`, pois não tem tabela):
- `GET /health/live` → `{"status": "ok"}`, sem tocar no banco (liveness p/ Docker/k8s).
- `GET /health/ready` → readiness: `HealthRepository.ping()` executa `SELECT 1` via `AsyncSession`; o service mede a latência e monta `HealthRead(status, database, latency_ms, version, environment)`. Banco fora do ar → `503` com `{"status": "degraded", "database": "down"}` (o service devolve o resultado; o controller escolhe o status code — 200 ou 503 — sem levantar exceção).
- `healthcheck` do `docker-compose` aponta para `/health/live`; `/health/ready` fica como `depends_on` de deploy.
- Testes: ready OK; ready com `ping()` falhando (override da dependência) → 503.

### 3. Módulo `users` (referência viva)
Implementar os 6 arquivos + `tests/` com CRUD completo: `create`, `get_by_id`, `list` (paginado com `limit/offset`), `update`, `delete`. Repository expõe também `get_by_email` (usado pelo auth). Service faz hash de senha e valida e-mail duplicado (`ConflictError`).

### 4. Módulo `auth`
- `app/core/security.py`: `hash_password`, `verify_password`, `create_access_token`, `create_refresh_token`, `decode_token`.
- `auth/service.py` consome `users` via `UserRepository` (dependência entre módulos acontece **service → repository de outro módulo**, nunca router → router).
- `app/api/deps.py`: `get_current_user` com `OAuth2PasswordBearer`.
- Rotas: `POST /auth/register`, `POST /auth/login`, `POST /auth/refresh`, `GET /auth/me`.

### 5. Alembic
`alembic/env.py` em modo async (`connectable.run_sync`), importando `app.database.base.Base` e `app.modules.*.models` para que `autogenerate` enxergue as tabelas. Gerar a migration inicial de `users`.

### 6. Docker
`Dockerfile` (python:3.11-slim + uv, non-root) e `docker-compose.yml` com `db` (postgres:16 + healthcheck + volume) e `api` (`depends_on: service_healthy`, hot-reload em dev). `Makefile` para os comandos usuais.

### 7. Testes
`tests/conftest.py`: engine de teste, criação/drop de schema por sessão, fixture `db_session` com transação revertida por teste, fixture `client` (`httpx.AsyncClient` + `ASGITransport`) com `app.dependency_overrides[get_session]`. Testes de `users` e `auth` (happy path + 404 + 409 + 401).

### 8. Camada `.claude/` — a parte central
- **`CLAUDE.md`** (root, ~30 linhas): stack, comandos essenciais, e a instrução dura: *"Antes de escrever qualquer código, leia `.claude/AGENTS.md`. Para criar um módulo novo, siga `.claude/skills/new-module/SKILL.md` sem improvisar."*
- **`.claude/AGENTS.md`**: tabela de camadas acima; convenções de nomes (`{Entity}Model`, `{Entity}Create/Update/Read`, `{Entity}Repository/Service/Controller`); padrão de rotas e status codes; onde colocar cada tipo de código com um índice "quero fazer X → edite o arquivo Y"; seção **Anti-padrões proibidos** (SQL no service, `HTTPException` no service, lógica no router, import circular entre módulos, `session.commit()` no repository); checklist final de PR.
- **`.claude/base_spec.md` — a especificação normativa da criação de rotas.** Documento deliberadamente burocrático: descreve *a única forma aceita* de nascer uma rota nova, e é rígido de propósito — o custo de seguir o rito é menor que o de revisar código improvisado por IA. Escrito com **MUST / NEVER** em cada regra, para não deixar margem a interpretação. Conteúdo:

  1. **Formulário de especificação da rota** (a IA preenche *antes* de escrever qualquer linha): método, path, se é pública ou autenticada, schema de entrada, schema de saída, status de sucesso, lista de erros possíveis com código, e efeitos colaterais no banco. Se algum campo não puder ser preenchido, a IA **MUST** parar e perguntar ao usuário em vez de adivinhar.
  2. **Ordem obrigatória de implementação — de baixo para cima, nunca o contrário:** `schemas` → `repository` → `service` → `controller` → `router` → registro em `app/api/v1.py` → testes → migration (quando houver mudança de tabela). Cada passo declara o que **MUST** existir no arquivo e o que **NEVER** pode aparecer nele.
  3. **Contrato de rota padronizado**: nomes no plural e kebab-case; verbos apenas por método HTTP (proibido `/users/create-user`); tabela fixa de status codes (`200` leitura, `201` criação + `Location`, `204` delete, `400` entrada inválida, `401`, `403`, `404`, `409` conflito, `422` do Pydantic, `503` dependência fora); formato único de erro `{"error": {"code", "message", "details"}}`; paginação sempre `limit`/`offset` com envelope `{"items", "total", "limit", "offset"}`.
  4. **Regras de assinatura**: toda função de rota é `async def`; `response_model` é obrigatório; `Depends(get_session)` vem do router e é repassado para baixo; nada de acessar `Request` fora do router.
  5. **Definition of Done** — checklist que **MUST** estar todo marcado antes de considerar a rota pronta: aparece no `/docs` com exemplos, tem teste de sucesso **e** de cada erro listado no formulário, `uv run pytest` verde, `uv run ruff check` limpo, migration gerada e aplicada, e nenhum anti-padrão do `AGENTS.md` presente.
  6. **Exemplo completo, ponta a ponta**, do formulário preenchido até os testes, usando `POST /products` — o mesmo `Product` de `.claude/examples/`, para os dois documentos se reforçarem.

  `CLAUDE.md`, `AGENTS.md` e a skill `new-module` **apontam para `base_spec.md` como leitura obrigatória** sempre que a tarefa envolver criar ou alterar rota.

- **`.claude/skills/new-module/SKILL.md`**: receita numerada — copiar `templates/module/`, substituir placeholders (`{{Entity}}`, `{{entity}}`, `{{entities}}`), registrar router em `app/api/v1.py`, importar models no `alembic/env.py`, `uv run alembic revision --autogenerate`, `uv run pytest`.

- **`.claude/examples/` — um exemplo por camada, cada um em pasta e arquivo próprios.** É o material de estudo: a IA abre **só a pasta da camada que vai escrever**, sem precisar carregar o projeto inteiro. Todas as pastas usam a mesma entidade fictícia `Product`, de ponta a ponta, para o exemplo ser coerente entre camadas.

  Cada pasta `NN-<camada>/` contém:
  - o **arquivo Python real e completo** (roda e faz sentido isolado, com comentários `# ✅ faça` / `# ❌ nunca aqui` nos pontos críticos);
  - um **`README.md` de uma página**: o que essa camada faz, o que ela pode importar, os 3–5 erros mais comuns, e a linha do fluxo indicando de onde vem e para onde vai (`← controller | → repository`).

  | Pasta | Arquivo | Ensina |
  |---|---|---|
  | `01-model/` | `example_model.py` | `Mapped`/`mapped_column`, herança de `Base` + `TimestampMixin`, `__tablename__`, índices, relacionamento |
  | `02-schema/` | `example_schemas.py` | `Create`/`Update`/`Read`, `model_config = ConfigDict(from_attributes=True)`, validators, `Update` com campos opcionais |
  | `03-repository/` | `example_repository.py` | `AsyncSession`, `select()`, `scalars().first()/all()`, paginação, `flush` vs `commit` |
  | `04-service/` | `example_service.py` | regra de negócio, `NotFoundError`/`ConflictError`, onde fica o `commit` |
  | `05-controller/` | `example_controller.py` | orquestração, conversão model → schema, quando escolher o status code |
  | `06-router/` | `example_router.py` | `APIRouter(prefix, tags)`, `response_model`, `status_code`, `Depends(get_session)`, rota protegida com `get_current_user` |
  | `07-tests/` | `test_example_api.py`, `test_example_service.py` | teste de rota com `AsyncClient` e teste de service com repository fake — os dois estilos, lado a lado |
  | `08-migration/` | `example_migration.py` | como é uma migration Alembic gerada, `upgrade`/`downgrade`, o que revisar antes de aplicar |

  `examples/README.md` é o índice de entrada: tabela "quero fazer X → leia a pasta Y" + o diagrama do fluxo de camadas. `AGENTS.md` e a skill `new-module` linkam para as pastas específicas em cada passo.

- **`.claude/templates/module/`**: os mesmos arquivos dos exemplos, porém genéricos com `{{Entity}}`, prontos para copiar num módulo novo (exemplos = ler e entender; templates = copiar e substituir).

## Verificação

1. `uv sync` e `docker compose up -d db && make migrate` (→ `uv run alembic upgrade head`) → tabelas criadas sem erro.
2. `uv run pytest` → toda a suíte verde.
3. `make run` e conferir `http://localhost:8000/docs` (Swagger com os grupos health/users/auth).
4. `curl localhost:8000/health/ready` → 200 com `database: "up"`; depois `docker compose stop db` e repetir → 503 com `database: "down"` (prova que o check é real, não estático).
5. Fluxo manual: `register` → `login` (recebe token) → `GET /auth/me` com `Bearer` → 200; sem token → 401; e-mail repetido → 409; id inexistente → 404.
6. **Teste do objetivo real:** em sessão limpa, pedir a um modelo fraco *"crie o módulo products"* seguindo apenas `CLAUDE.md`; ele deve chegar sozinho ao `base_spec.md`, preencher o formulário da rota e produzir código que compila, passa no lint e vem com testes — sem intervenção. Conferir o resultado contra a Definition of Done do `base_spec.md`; qualquer item que a IA tenha pulado indica uma regra que precisa ficar mais explícita no documento.

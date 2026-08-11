# AGENTS.md — como trabalhar neste projeto

**Leia este arquivo por completo antes de escrever qualquer linha de código.**

Este é o documento de entrada para qualquer agente de IA (Claude Code, Cursor,
Copilot, Codex, Windsurf, Aider…) ou pessoa que for desenvolver aqui.

- Este arquivo diz **como escrever o código** (arquitetura).
- [`.rules/`](.rules/README.md) diz **o que o sistema deve fazer** (negócio).

Estas regras não são sugestões. Código que as viola deve ser corrigido, não
justificado. Na dúvida entre seguir a regra e "fazer diferente porque é melhor
neste caso": siga a regra.

---

## 0. Mapa dos documentos

| Documento | Responde |
|---|---|
| **`AGENTS.md`** (este arquivo) | como escrever o código |
| [`docs/specs/<ID>-<slug>/SPEC.md`](docs/specs/README.md) | **o que** construir nesta tarefa (vem do refinamento) |
| [`.claude/task_spec.md`](.claude/task_spec.md) | como preencher uma spec de tarefa |
| [`.claude/base_spec.md`](.claude/base_spec.md) | o rito obrigatório para criar/alterar uma rota |
| [`.rules/`](.rules/README.md) | as regras de negócio, com ID rastreável |
| `.claude/skills/<camada>/` | regra + exemplo + template de cada camada |
| `CLAUDE.md` | ponteiro curto para este arquivo |

**Se a tarefa tiver uma spec** (`docs/specs/<ID>-<slug>/`), ela é o ponto de
partida: leia o `SPEC.md` **e** o `TODO.md` da pasta antes de codar. A spec diz
o que construir; este arquivo e o `base_spec.md` dizem como.

### Onde ficam os templates

Cada camada tem sua própria pasta em `.claude/skills/`, e **dentro dela** estão
os três arquivos que você precisa:

```
.claude/skills/<camada>/
├── SKILL.md          # a regra da camada: o que MUST e o que NEVER
├── example.py        # exemplo real e comentado (entidade Product)
└── template.py.tpl   # esqueleto com placeholders, para copiar
```

Camadas disponíveis: `model`, `schema`, `repository`, `service`, `controller`,
`router`, `tests`, `migration`, e o roteiro orquestrador `new-module`.

### Onde ficam as regras de negócio

`.rules/` espelha `app/modules/`: **uma pasta por módulo**, cada uma com um
`RULES.md`.

```
.rules/
├── README.md              # formato obrigatório de cada regra
├── _global/RULES.md       # regras válidas para todos os módulos
├── users/RULES.md
└── auth/RULES.md
```

Módulo novo ganha `.rules/<modulo>/RULES.md`. As regras têm ID (`RN-USERS-002`)
citado no `service.py` e no teste, então `grep -r RN-USERS-002 .` mostra a
regra, a implementação e o teste.

Placeholders dos templates:

| Placeholder | Vira | Exemplo |
|---|---|---|
| `{{Entity}}` | PascalCase singular | `Product` |
| `{{entity}}` | snake_case singular | `product` |
| `{{entities}}` | snake_case plural | `products` |
| `{{ENTITIES}}` | UPPER plural (IDs de regra) | `PRODUCTS` |

### Se o template não existir

Pode acontecer de você precisar de algo que não tem template (uma camada nova,
um caso não previsto, ou a pasta `.claude/skills/` não estar disponível na sua
ferramenta). Nesse caso, **em ordem de preferência**:

1. **Copie do módulo `users`.** Ele é a implementação de referência completa e
   sempre está no repositório: `app/modules/users/{models,schemas,repository,service,controller,router}.py`
   e `tests/test_users.py`. O que estiver lá é o padrão correto.
2. **Se o caso não existe em `users`, olhe `auth`** (dependência entre módulos,
   rota pública vs. protegida) ou `health` (módulo sem tabela, escolha manual de
   status code).
3. **Se ainda assim não houver precedente, PARE e pergunte ao usuário.**
   Descreva as opções que você considerou e por quê. **Não invente um padrão
   novo em silêncio** — um padrão inventado se propaga para todos os módulos
   seguintes e é caro de desfazer.

A mesma regra vale se `.claude/base_spec.md` ou `.rules/` não existirem no
checkout: siga a estrutura de `users`, e pergunte antes de decidir qualquer
contrato de API que não tenha precedente no código.

---

## 1. A regra única: dependência sempre para baixo

```
HTTP -> router.py -> controller.py -> service.py -> repository.py -> models.py
                                          |
                                      schemas.py
```

**Cada camada só chama a camada imediatamente abaixo.** Nunca pule uma camada,
nunca chame para cima.

| Arquivo | Responsabilidade | Pode importar | NUNCA faz |
|---|---|---|---|
| `router.py` | path, método, status code, `response_model`, dependências | controller, schemas, deps | lógica, SQLAlchemy, try/except de negócio |
| `controller.py` | orquestra, converte model -> schema de saída | service, schemas | query SQL, regra de negócio |
| `service.py` | regra de negócio, validações, decide o `commit` | repository, schemas, exceptions, security | `HTTPException`, `Request`, `select()` |
| `repository.py` | monta query, usa a sessão | models, `AsyncSession` | regra de negócio, `commit()` |
| `models.py` | mapeamento de tabela | `app.database.base` | Pydantic, lógica |
| `schemas.py` | contratos de entrada/saída | pydantic | SQLAlchemy |

### Por que assim
Regra de negócio testável sem HTTP; troca de banco isolada no repository; rota
legível como documentação. Quebrar a ordem faz o código voltar a ser um
`main.py` de 2000 linhas.

---

## 2. Índice: quero fazer X -> onde vou

| Quero... | Skill | Arquivo que edito |
|---|---|---|
| criar um módulo inteiro | `new-module` | `app/modules/<modulo>/` |
| criar/alterar uma rota | leia `base_spec.md`, skill `router` | `app/modules/<modulo>/router.py` |
| criar uma tabela | skill `model` + `migration` | `models.py` + `alembic/versions/` |
| mudar o corpo de entrada/saída | skill `schema` | `schemas.py` |
| escrever uma consulta ao banco | skill `repository` | `repository.py` |
| implementar uma regra de negócio | skill `service` + `.rules/` | `service.py` |
| escrever teste | skill `tests` | `tests/test_<modulo>.py` |
| adicionar variável de ambiente | — | `app/core/config.py` + `.env.example` |
| adicionar erro de domínio novo | — | `app/core/exceptions.py` |
| registrar o router de um módulo novo | — | `app/api/v1.py` |

---

## 3. Convenções de nome

| Coisa | Padrão | Exemplo |
|---|---|---|
| Pasta do módulo | plural, snake_case | `app/modules/products/` |
| Model | `{Entity}Model` | `ProductModel` |
| Tabela | plural, snake_case | `products` |
| Schemas | `{Entity}Create`, `{Entity}Update`, `{Entity}Read` | `ProductCreate` |
| Repository | `{Entity}Repository` | `ProductRepository` |
| Service | `{Entity}Service` | `ProductService` |
| Controller | `{Entity}Controller` | `ProductController` |
| Router | variável `router`, com `prefix="/products"` | — |
| Teste | `test_<acao>_<resultado_esperado>` | `test_email_duplicado_retorna_409` |

Comentários e docstrings **no código** são em português sem acentos (evita
problema de encoding em log e terminal). Documentação `.md` usa acentos
normalmente. Não use emoji em arquivos `.py`.

---

## 4. Transação: quem faz o quê

- **Repository** usa `flush()` — garante o INSERT e popula o `id`.
- **Service** chama `commit()` — só ele conhece o limite da operação.
- Depois de um `UPDATE`, o service chama `repository.refresh(obj)` para
  recarregar colunas com `onupdate` server-side (`updated_at`). Sem isso o
  Pydantic quebra com `MissingGreenlet`.

---

## 5. Erros

Service lança **erro de domínio**; o handler global em `app/main.py` traduz para HTTP.

| Exceção (`app/core/exceptions.py`) | HTTP |
|---|---|
| `DomainValidationError` | 400 |
| `UnauthorizedError` | 401 |
| `ForbiddenError` | 403 |
| `NotFoundError` | 404 |
| `ConflictError` | 409 |
| `ServiceUnavailableError` | 503 |

Toda resposta de erro sai como `{"error": {"code", "message", "details"}}` (RN-GLOBAL-004).

---

## 6. Anti-padrões proibidos

| NUNCA faça isto | FAÇA isto |
|---|---|
| `select()` ou `session.execute()` fora do repository | mova a query para o repository |
| `raise HTTPException(...)` no service | `raise NotFoundError(...)` e deixe o handler traduzir |
| lógica de negócio no router ou no controller | mova para o service |
| `session.commit()` dentro do repository | o service decide quando commitar |
| importar router/controller de outro módulo | dependa do **repository** ou do **service** do outro módulo |
| `os.environ[...]` espalhado no código | declare em `app/core/config.py` e use `settings` |
| model do SQLAlchemy retornado direto pela rota | converta com `{Entity}Read.model_validate(obj)` |
| `hashed_password` em schema de saída | RN-GLOBAL-005: segredo nunca sai na resposta |
| rota sem `response_model` | sempre declare o `response_model` |
| regra de negócio não escrita em `.rules/` | escreva a regra primeiro, depois implemente |
| `def` (síncrono) numa rota | toda rota é `async def` |
| inventar um padrão porque o template não existe | copie de `users`, ou pergunte (seção 0) |

---

## 7. Comandos

Todo comando roda por **`uv`**. Não há Makefile, script wrapper nem atalho:
o comando que você lê aqui é o comando que executa.

```bash
uv sync                                    # instala as dependencias

uv run uvicorn app.main:app --reload       # API em http://localhost:8000/docs

uv run pytest                              # testes
uv run pytest -v                           # testes com detalhe
uv run pytest tests/test_users.py -k nome  # um teste especifico

uv run ruff check .                        # lint
uv run ruff format .                       # formata
uv run ruff check --fix .                  # corrige o que da para automatizar

uv run alembic upgrade head                              # aplica migrations
uv run alembic revision --autogenerate -m "descricao"    # gera migration
uv run alembic current                                   # revisao atual do banco

docker compose up -d --build               # api + postgres
docker compose down
```

**Antes de abrir PR**, os dois que importam:

```bash
uv run ruff check . && uv run pytest
```

Gerenciador de dependências é **`uv`** (nunca `pip install` avulso, nunca
`requirements.txt`; libs novas entram com `uv add` / `uv add --dev`).
Testes são **`pytest`** (nunca `unittest`).

---

## 8. Checklist antes de abrir PR

- [ ] `uv run ruff check .` limpo e `uv run pytest` verde
- [ ] Toda regra de negócio nova está em `.rules/` com ID, e o ID é citado no service e no teste
- [ ] Nenhum item da seção 6 aparece no diff
- [ ] Rota nova aparece corretamente em `/docs`
- [ ] Mudou model? Existe migration e ela foi aplicada
- [ ] Módulo novo? Router registrado em `app/api/v1.py` e model importado em `alembic/env.py`
- [ ] A Definition of Done de [`.claude/base_spec.md`](.claude/base_spec.md) está toda marcada

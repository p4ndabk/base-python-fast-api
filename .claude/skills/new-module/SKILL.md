---
name: new-module
description: Roteiro completo para criar um módulo novo (ex. products, orders) neste projeto FastAPI, do formulário de especificação até os testes passando. Use sempre que precisar adicionar uma entidade ou conjunto de rotas novo.
---

# Criar um módulo novo

Esta skill é o **roteiro orquestrador**: ela não ensina nenhuma camada, ela diz
em que ordem invocar as outras skills e o que fazer entre elas.

Não pule etapas e não mude a ordem. A ordem é de baixo para cima porque começar
pelo router leva a inventar contratos que a camada de baixo não sustenta.

---

## Etapa 0 — Especificação (antes de criar qualquer arquivo)

0. Se ainda não leu nesta sessão, leia [`AGENTS.md`](../../../AGENTS.md) na raiz —
   as regras de arquitetura e os anti-padrões proibidos.
1. Leia [`.claude/base_spec.md`](../../base_spec.md).
2. Preencha o **formulário de especificação** de cada rota do módulo e cole na
   sua resposta.
3. Se alguma rota aplica regra de negócio nova, escreva a regra em
   `.rules/<modulo>/RULES.md` **agora**, com ID (`RN-<MODULO>-001`) — crie a pasta.
   Se faltar informação para preencher qualquer campo: **pare e pergunte.**

---

## Etapa 1 — Estrutura

```bash
mkdir -p app/modules/<modulo>
touch app/modules/<modulo>/__init__.py
```

Nome da pasta: **plural, snake_case** (`products`, `order_items`).

---

## Etapa 2 — Camadas, nesta ordem

Para cada camada: invoque a skill, copie o `template.py.tpl` da pasta dela,
substitua os placeholders e ajuste ao seu caso.

| # | Skill | Arquivo criado |
|---|---|---|
| 1 | `schema` | `app/modules/<modulo>/schemas.py` |
| 2 | `model` | `app/modules/<modulo>/models.py` |
| 3 | `repository` | `app/modules/<modulo>/repository.py` |
| 4 | `service` | `app/modules/<modulo>/service.py` |
| 5 | `controller` | `app/modules/<modulo>/controller.py` |
| 6 | `router` | `app/modules/<modulo>/router.py` |

Placeholders dos templates:

| Placeholder | Vira | Exemplo |
|---|---|---|
| `{{Entity}}` | PascalCase singular | `Product` |
| `{{entity}}` | snake_case singular | `product` |
| `{{entities}}` | snake_case plural | `products` |
| `{{ENTITIES}}` | UPPER plural (IDs de regra) | `PRODUCTS` |

---

## Etapa 3 — Registro (os dois esquecimentos clássicos)

**3.1 — Router em `app/api/v1.py`:**
```python
from app.modules.products.router import router as products_router
api_router.include_router(products_router)
```
Sem isso a rota não existe e o `/docs` não mostra nada.

**3.2 — Model em `alembic/env.py`:**
```python
from app.modules.products import models as products_models  # noqa: F401
```
Sem isso o `--autogenerate` gera uma migration vazia.

---

## Etapa 4 — Migration

Invoque a skill `migration`.

```bash
uv run alembic revision --autogenerate -m "cria tabela products"
# ABRA o arquivo gerado em alembic/versions/ e revise
uv run alembic upgrade head
```

---

## Etapa 5 — Testes

Invoque a skill `tests`. Crie `tests/test_<modulo>.py` com:
- um teste de sucesso por rota;
- um teste para **cada** erro listado no formulário da Etapa 0;
- o ID da regra no docstring do teste que a cobre.

---

## Etapa 6 — Verificação final

```bash
uv run ruff check . && uv run pytest      # tem que estar limpo e verde
uv run uvicorn app.main:app --reload      # confira as rotas em http://localhost:8000/docs
```

Percorra a **Definition of Done** de [`base_spec.md`](../../base_spec.md) item
por item. Só considere o módulo pronto quando todos estiverem marcados.

---

## Resumo em uma tela

```
formulário → .rules/ → schemas → models → repository → service → controller
   → router → v1.py → alembic/env.py → migration → testes → ruff + pytest
```

Em caso de dúvida sobre um padrão, o módulo `users` no repositório é a
implementação de referência completa deste roteiro.

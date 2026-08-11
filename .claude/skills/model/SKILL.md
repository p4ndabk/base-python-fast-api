---
name: model
description: Como escrever a camada de model (tabela SQLAlchemy) deste projeto. Use ao criar ou alterar uma tabela, adicionar coluna, índice ou relacionamento em app/modules/<modulo>/models.py.
---

# Camada: model

`← repository | → banco de dados`

O model é **só o mapeamento da tabela**. Nada mais.

## Arquivos desta pasta
- `example.py` — o model de `Product`, completo e comentado
- `template.py.tpl` — o mesmo arquivo com `{{Entity}}` para copiar

## O que MUST estar aqui
- `class {Entity}Model(Base, TimestampMixin)` — sempre os dois pais
- `__tablename__` no plural, snake_case
- Colunas com `Mapped[tipo]` + `mapped_column(...)`
- `index=True` em coluna usada em `WHERE` frequente
- `unique=True` em coluna com unicidade **estrutural** (o banco é a última linha de defesa)

## O que NEVER pode aparecer
- Pydantic (`BaseModel`, validators) — isso é `schemas.py`
- Regra de negócio, cálculo, método que decide algo — isso é `service.py`
- `select()`, sessão, query — isso é `repository.py`
- Redeclarar `id`, `created_at`, `updated_at` — já vêm do `TimestampMixin`

## Erros mais comuns
1. **Esquecer de importar o model em `alembic/env.py`** → `--autogenerate` gera migration vazia. É o erro nº 1.
2. Usar `Column(...)` no estilo antigo em vez de `Mapped[...] / mapped_column(...)`.
3. Colocar unicidade só no service e não no banco — corrida entre dois requests cria duplicata mesmo assim.
4. `nullable` divergindo do schema Pydantic (campo obrigatório no schema, `nullable=True` na tabela).
5. Usar `String` sem tamanho em Postgres onde há limite conhecido.

## Depois de mexer aqui
1. Importe o `models` do módulo em `alembic/env.py`
2. `uv run alembic revision --autogenerate -m "descricao"` e **revise** o arquivo gerado
3. `uv run alembic upgrade head`
4. Vá para a skill `schema`

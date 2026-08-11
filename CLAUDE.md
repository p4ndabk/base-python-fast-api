# CLAUDE.md

## Regra número 1

**Leia [`AGENTS.md`](AGENTS.md) na raiz do projeto antes de escrever qualquer
linha de código.** Ele contém as regras de arquitetura, os anti-padrões
proibidos, onde ficam os templates de cada camada e o que fazer quando o
template que você precisa não existir.

Não comece a codar sem ter lido. Não improvise um padrão que não esteja lá —
se não houver precedente, pergunte.

## Atalhos

| Se você vai... | Leia / invoque |
|---|---|
| escrever **qualquer** código | [`AGENTS.md`](AGENTS.md) |
| criar ou alterar uma **rota** | [`.claude/base_spec.md`](.claude/base_spec.md) |
| implementar uma **regra de negócio** | [`.rules/`](.rules/README.md) |
| criar um **módulo novo** | skill `new-module` |
| escrever **uma camada** | skill `model`, `schema`, `repository`, `service`, `controller`, `router`, `tests` ou `migration` |

## O essencial

Stack: Python 3.11 · FastAPI · SQLAlchemy 2.0 async · PostgreSQL · Alembic · uv · pytest

```
router.py -> controller.py -> service.py -> repository.py -> models.py
```

Cada camada só chama a camada imediatamente abaixo. A tabela completa de
responsabilidades está no `AGENTS.md`.

```bash
uv run uvicorn app.main:app --reload    # http://localhost:8000/docs
uv run pytest                           # testes
uv run ruff check . && uv run pytest    # antes de abrir PR
```

Todo comando roda por `uv`. Não há Makefile — a lista completa está na seção 7
do `AGENTS.md`.

Referência viva de como um módulo deve ficar: `app/modules/users/`.

---
name: migration
description: Como criar, revisar e aplicar migrations Alembic neste projeto. Use ao criar tabela, adicionar/remover coluna ou índice, ou quando o autogenerate gerar uma migration vazia ou errada.
---

# Camada: migration

`← models.py | → banco de dados`

Migration é o histórico versionado do schema. É o único artefato do projeto que
**não pode ser reescrito** depois de aplicado em outro ambiente.

## Arquivos desta pasta
- `example.py` — uma migration comentada, mostrando o que revisar

## Fluxo obrigatório

```bash
# 1. o model já existe em app/modules/<modulo>/models.py
# 2. IMPORTE o models em alembic/env.py   <- o passo que todo mundo esquece
# 3. gere
uv run alembic revision --autogenerate -m "cria tabela products"
# 4. ABRA o arquivo gerado em alembic/versions/ e revise
# 5. aplique
uv run alembic upgrade head
```

## Regra nº 1: `--autogenerate` não é confiável sozinho

Você **MUST** abrir e revisar o arquivo gerado. O autogenerate:

| Detecta | Não detecta |
|---|---|
| tabela nova / removida | renomear tabela (vira DROP + CREATE, **perde os dados**) |
| coluna nova / removida | renomear coluna (idem) |
| mudança de tipo (com `compare_type=True`) | mudança só de `server_default` |
| índices e constraints nomeadas | dados existentes que violam uma nova constraint |

## Migration vazia? O model não foi importado

Sintoma: `upgrade()` só tem `pass`.
Causa: o model não está em `alembic/env.py`. Adicione:

```python
from app.modules.products import models as products_models  # noqa: F401
```

## O que MUST estar na migration
- `upgrade()` e `downgrade()` — o `downgrade` desfaz **exatamente** o que o `upgrade` faz, na ordem inversa
- Coluna `NOT NULL` em tabela com dados: `server_default` ou três passos (adiciona nullable → preenche → torna NOT NULL)

## O que NEVER pode acontecer
- Editar migration já aplicada em outro ambiente — crie uma nova
- `downgrade()` com `pass` "porque não vou precisar"
- Adicionar `NOT NULL` sem default em tabela populada — quebra na hora de aplicar
- Escrever DML de carga pesada de dados aqui — migration é schema

## Comandos
```bash
uv run alembic current              # em que revisão o banco está
uv run alembic history              # histórico
uv run alembic upgrade head         # aplica tudo
uv run alembic upgrade head --sql   # SÓ imprime o SQL, não aplica (ótimo para revisar)
uv run alembic downgrade -1         # volta uma revisão
```

## Erros mais comuns
1. Esquecer o import em `alembic/env.py` → migration vazia.
2. Renomear coluna via autogenerate e perder os dados em produção.
3. `downgrade()` incompleto — impede rollback.
4. Duas branches criando migrations em paralelo → múltiplos heads. Resolva com `alembic merge heads`.
5. Aplicar sem ler o SQL. Use `--sql` para conferir antes.

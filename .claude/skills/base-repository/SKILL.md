---
name: base-repository
description: Como escrever a camada de repository (acesso a dados com SQLAlchemy async) deste projeto. Use ao criar consultas, paginação, inserção ou remoção em app/modules/<modulo>/repository.py.
---

# Camada: repository

`← service | → models.py / AsyncSession`

O repository é o **único** lugar do módulo que conhece SQL. Ele lê e escreve —
não decide nada.

## Arquivos desta pasta
- `example.py` — o repository de `Product`, completo e comentado
- `template.py.tpl` — o mesmo arquivo com `{{Entity}}` para copiar

## O que MUST estar aqui
- `def __init__(self, session: AsyncSession)`
- Métodos que devolvem **model ou `None`**, nunca erro de domínio
- `select()` + `await self.session.execute(...)` + `.scalars().first()` / `.all()`
- `flush()` depois de `add()` — garante o INSERT e popula o `id`
- `count()` separado quando a listagem é paginada
- `refresh(obj)` para recarregar colunas `onupdate` server-side

## O que NEVER pode aparecer
- `commit()` — quem commita é o **service**
- `raise NotFoundError(...)` — devolva `None` e deixe o service decidir
- `if` de regra de negócio
- `HTTPException`, `Request`, qualquer coisa de `fastapi`

## `flush` vs `commit` — a confusão nº 1

| | O que faz | Quem chama |
|---|---|---|
| `flush()` | manda o SQL para o banco dentro da transação; popula `id` e defaults | **repository** |
| `commit()` | encerra a transação, torna permanente | **service** |
| `refresh(obj)` | relê o objeto do banco | **repository** (chamado pelo service após UPDATE) |

Se o repository desse `commit()`, o service perderia a capacidade de agrupar
duas escritas numa única transação atômica.

## Erros mais comuns
1. Dar `commit()` aqui — quebra a atomicidade de operações compostas.
2. `.scalars().first()` vs `.scalar_one()`: `first()` devolve `None` se não achar; `scalar_one()` **explode**. Use `first()`.
3. Esquecer `await` no `session.execute(...)`.
4. Fazer paginação em Python (`[offset:offset+limit]` depois de carregar tudo) em vez de `.limit().offset()` no SQL.
5. Devolver `Result` cru em vez de model — o service não deve conhecer a API do SQLAlchemy.
6. N+1: carregar relacionamento em loop. Use `selectinload()` quando precisar do relacionamento.

## Depois de mexer aqui
Vá para a skill `base-service`.

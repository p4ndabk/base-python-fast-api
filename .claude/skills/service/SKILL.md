---
name: service
description: Como escrever a camada de service (regra de negócio) deste projeto. Use ao implementar validações que dependem do banco, decisões de domínio, transações ou qualquer regra RN-* de .rules/ em app/modules/<modulo>/service.py.
---

# Camada: service

`← controller | → repository.py`

O service é **o coração do sistema**: a única camada onde regra de negócio pode
morar. Ele não sabe que existe HTTP e não sabe montar SQL.

## Leitura obrigatória antes de escrever
[`.rules/`](../../../.rules/README.md) — as regras de negócio do sistema.
Se a regra que você vai implementar não está escrita lá, **escreva-a primeiro**.

## Arquivos desta pasta
- `example.py` — o service de `Product`, completo e comentado
- `template.py.tpl` — o mesmo arquivo com `{{Entity}}` para copiar

## O que MUST estar aqui
- `def __init__(self, repository: {Entity}Repository)`
- Cada regra implementada com o **ID citado em comentário**: `# RN-PRODUCTS-001: ...`
- Erros de domínio: `NotFoundError`, `ConflictError`, `DomainValidationError`, `UnauthorizedError`
- `await self.repository.session.commit()` ao final de cada operação de escrita
- `await self.repository.refresh(obj)` depois de um UPDATE

## O que NEVER pode aparecer
- `from fastapi import ...` — nada de `HTTPException`, `Depends`, `Request`, `Response`
- `select()`, `session.execute()` — peça um método ao repository
- Conversão para schema de saída — isso é do controller (o service devolve **model**)

## Por que o service não pode conhecer HTTP
Porque a regra tem que ser testável sem subir servidor, e a mesma regra precisa
valer se amanhã ela for chamada por um worker, um comando CLI ou uma fila.
Ao lançar `ConflictError`, o handler global em `app/main.py` transforma em 409 —
o service não precisa saber disso.

## Erros mais comuns
1. `raise HTTPException(status_code=404)` — use `NotFoundError`.
2. Esquecer o `commit()` — o teste passa (a sessão do teste ainda vê o objeto) e o dado some em produção.
3. Esquecer `refresh()` depois de UPDATE → `MissingGreenlet` ao serializar `updated_at`.
4. Implementar regra que não está em `.rules/` — regra invisível é regra perdida.
5. Devolver `{Entity}Read` em vez do model — a conversão é do controller.
6. Chamar o **service** de outro módulo em vez do **repository** dele, criando import circular.

## Dependência entre módulos
Permitido: `AuthService` usa `UserRepository`.
Proibido: importar `router.py` ou `controller.py` de outro módulo.
Veja `app/modules/auth/service.py` como referência.

## Depois de mexer aqui
Vá para a skill `controller`.

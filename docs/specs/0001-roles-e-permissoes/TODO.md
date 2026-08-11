# Pendências técnicas — 0001 Roles e Permissions

## Abertas

### PT-01 — Bootstrap do primeiro usuário com `roles:manage`
**O quê:** a migration cria a role `admin` com a permission `roles:manage`,
mas não atribui essa role a nenhum usuário. Sem isso, ninguém consegue
chamar `POST /roles` ou `PUT /roles/{id}/permissions` depois do deploy.
**Por que ficou de fora:** depende de decisão de produto (dúvida #2 do
`SPEC.md`) sobre quem é o admin inicial e como esse acesso é concedido —
script de seed com e-mail fixo, comando de CLI, ou update manual no banco.
**Onde:** migration de seed em `alembic/versions/` + possível comando novo.
**Impacto se continuar assim:** ambiente novo (dev, staging) nasce sem
ninguém conseguindo gerenciar roles; primeira atribuição precisa ser feita
via `UPDATE users SET role_id = ...` direto no banco.
**Esforço estimado:** baixo.
**Work item:** não criado.

### PT-02 — Aplicar `RequirePermission` nas rotas existentes
**O quê:** hoje `products`, `users` e `auth` usam só `CurrentUserDep`
(autenticado = autorizado). Depois desta tarefa, decidir quais permissions
cada rota exige e trocar `CurrentUserDep` por `RequirePermission(code)` onde
fizer sentido.
**Por que ficou de fora:** decisão de quais permissions cada módulo exige é
de produto/negócio, módulo a módulo — misturar com a entrega do mecanismo
atrasaria esta tarefa sem necessidade.
**Onde:** `app/modules/users/router.py`, `app/modules/products/router.py`
(quando existir).
**Impacto se continuar assim:** o sistema tem o mecanismo de autorização
pronto mas nenhuma rota de negócio o usa — "autenticado" continua
equivalendo a "pode tudo".
**Esforço estimado:** baixo por módulo, feito incrementalmente.
**Work item:** não criado.

### PT-03 — Usuário com múltiplas roles (N:N)
**O quê:** se a dúvida #1 do `SPEC.md` for respondida com "sim, precisa de
N:N", o modelo atual (`users.role_id` único) precisa virar uma tabela
associativa `user_roles`.
**Por que ficou de fora:** o pedido original foi 1 role por usuário; virar
N:N antes de confirmar a necessidade real é over-engineering.
**Onde:** `app/modules/users/models.py` (`role_id`), migration nova.
**Impacto se continuar assim:** se a necessidade aparecer depois, é uma
migration aditiva (não é breaking change no contrato de leitura, já que
`UserRead` pode expor uma lista mesmo com FK única hoje) — risco baixo de
adiar.
**Esforço estimado:** médio.
**Work item:** não criado.

---

## Resolvidas

| ID | Título | Resolvida em | Onde |
|---|---|---|---|
| | | | |

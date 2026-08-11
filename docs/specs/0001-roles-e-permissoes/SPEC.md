# 0001 — Roles e Permissions (autorizacao por papel)

## 1. Identificação

| Campo | Valor |
|---|---|
| **Work item (Azure DevOps)** | #____ — TBD (nao informado no pedido) |
| **Tipo** | Feature |
| **Épico / Feature pai** | — |
| **Módulo afetado** | `app/modules/roles` (novo), `app/modules/permissions` (novo), `app/modules/users` (alterado: ganha `role_id`), `app/api/deps.py` (alterado: novo helper de autorizacao), `app/core/permissions.py` (novo: enum `PermissionCode`), `app/core/security.py` (alterado: token carrega role/permissions), `app/modules/auth` (alterado: emissão de token busca role/permissions) |
| **P.O.** | — |
| **Tech Lead** | — |
| **Data do refinamento** | 2026-08-11 |
| **Depende de** | nada |

## 2. Contexto e objetivo

**Problema:** hoje toda rota protegida so verifica "esta autenticado?"
(`CurrentUserDep`). Nao existe forma de dizer "autenticado, mas so quem tem
tal permissao pode chamar esta rota" — a unica alternativa seria se cada
service comecar a fazer `if user.email == "admin@...":` espalhado pelo
codigo, o que e exatamente o anti-padrao que o `AGENTS.md` proibe (regra de
negocio fora do lugar, decisao de autorizacao duplicada por modulo).

**Objetivo:** um usuario pertence a uma role; uma role agrupa varias
permissions; um helper de dependencia (`RequirePermission(PermissionCode.X)`)
decide, de forma centralizada, se o usuario autenticado pode chamar a rota.
O catalogo de codigos de permission NAO e string livre: vive num enum
`PermissionCode` (`app/core/permissions.py`), unica fonte de verdade tanto
para o seed da migration quanto para o `RequirePermission(...)` usado nos
routers — evita erro de digitacao (`"prodcuts:create"`) que so um teste E2E
pegaria. Modulos futuros (products, orders, etc.) passam a proteger rotas
assim:

```python
# app/core/permissions.py
from enum import Enum


class PermissionCode(str, Enum):
    ROLES_MANAGE = "roles:manage"
    PERMISSIONS_READ = "permissions:read"
    PRODUCTS_CREATE = "products:create"
    # todo modulo que passa a exigir permission adiciona seu membro aqui,
    # e SO aqui - nunca uma string solta em outro arquivo.


# app/modules/products/router.py
from app.api.deps import CurrentUserDep, RequirePermission, SessionDep
from app.core.permissions import PermissionCode


async def create_product(
    data: ProductCreate,
    session: SessionDep,
    current_user: CurrentUserDep,
    _: Annotated[None, Depends(RequirePermission(PermissionCode.PRODUCTS_CREATE))],
) -> ProductRead: ...
```

Além de proteger rotas, o **access token JWT passa a carregar a role e as
permissions do usuário como claims**, emitidas no momento do login/refresh:

```json
{
  "sub": "3f2b1c4d-5e6f-4a7b-8c9d-0e1f2a3b4c5d",
  "type": "access",
  "role": "admin",
  "permissions": ["roles:manage", "permissions:read"],
  "iat": 1755000000,
  "exp": 1755001800
}
```

Isso evita que o front (ou outro serviço que só tem o token, sem acesso ao
banco) precise chamar `GET /auth/me` só para saber o que o usuário pode
fazer. **Importante:** essas claims são só para leitura/introspecção — a
decisão de autorização em `RequirePermission` continua consultando o banco
a cada request (ver regra 8 e decisão correspondente na seção 9), então uma
claim desatualizada no token nunca libera acesso indevido.

**Quem usa:** qualquer rota protegida do sistema, hoje e nos módulos
futuros; administradores (via API de roles) decidem quem tem qual permissao;
o front consome as claims do token para esconder/mostrar UI sem round-trip
extra.

## 3. Escopo — o que entra

- [ ] Enum `PermissionCode` em `app/core/permissions.py` (`str, Enum`):
      único lugar do código onde um código de permission é escrito por
      extenso. Todo `RequirePermission(...)` e todo seed referenciam esse
      enum — nenhum módulo escreve `"products:create"` como string solta.
- [ ] Entidade `Permission`: catálogo de permissões persistido (`code`
      único, populado a partir de `PermissionCode`), somente leitura via
      API — o catálogo nasce de uma migration com seed, não é criado em
      runtime.
- [ ] Entidade `Role`: nome único, descrição, CRUD completo via API.
- [ ] Associação N:N `Role <-> Permission` (tabela `role_permissions`),
      substituível de uma vez via `PUT /roles/{id}/permissions`.
- [ ] `UserModel` ganha `role_id` (FK nullable para `roles.id`); usuário sem
      role não tem nenhuma permissão (fail closed).
- [ ] Atribuir/trocar/remover a role de um usuário via `PATCH /users/{id}`
      (campo `role_id` novo em `UserUpdate`, já opcional).
- [ ] `UserRead` ganha `role_id` **e** `role` (objeto completo, com
      `permissions`) — RN-USERS-006. Evita o cliente ter que fazer um
      `GET /roles/{role_id}` extra só para saber o que o usuário pode fazer.
- [ ] Helper `RequirePermission(code: PermissionCode)` em `app/api/deps.py`:
      dependência FastAPI reutilizável por qualquer módulo, que verifica se
      `current_user.role` tem a permission `code.value`. Assinatura tipada
      no enum — passar uma string solta é erro de tipo, não só de runtime.
- [ ] `GET /permissions`: lista o catálogo (autenticado).
- [ ] `GET /roles`, `GET /roles/{id}`, `POST /roles`, `PATCH /roles/{id}`,
      `DELETE /roles/{id}`.
- [ ] Migration com seed inicial: itera sobre `PermissionCode` para
      popular `permissions`, e cria uma role `admin` com
      `PermissionCode.ROLES_MANAGE` e `PermissionCode.PERMISSIONS_READ`.
- [ ] `create_access_token` (`app/core/security.py`) ganha os parâmetros
      `role: str | None` e `permissions: list[str]`, gravados como claims
      `role` e `permissions` no payload do JWT. `AuthService._issue_tokens`
      busca a role e as permissions atuais do usuário (via `RoleRepository`)
      antes de emitir o token — tanto no login quanto no refresh.

## 4. Fora de escopo

- Aplicar `RequirePermission` retroativamente nas rotas já existentes de
  `users`/`auth`/`products` — cada módulo decide, numa tarefa própria, quais
  permissions suas rotas exigem. Aqui só entra o mecanismo.
- Usuário com múltiplas roles (N:N `User <-> Role`) — o pedido original foi
  "usuário pode estar em uma role"; modelo é 1 role por usuário. Se a
  necessidade real for N:N, é decisão de produto para outra tarefa (ver
  dúvida #1).
- Criar/editar `Permission` via API — o catálogo é fixo no enum
  `PermissionCode` + migration, porque cada `code` só faz sentido se um
  `RequirePermission(...)` real existir em alguma rota; permission "solta"
  sem rota associada é lixo, e string livre via API reabriria o problema
  de digitação que o enum existe para fechar.
- Flag `is_superuser` / bypass de checagem — todo acesso passa pela role.
  Bootstrap do primeiro admin é feito via migration (seed), não via flag.
- Cache de permissões por request/sessão — cada checagem consulta o banco;
  otimização fica para quando (se) houver problema de performance real.
- Hierarquia de roles (role herdar permissions de outra role).

## 5. Regras de negócio

| # | Regra | Quando é avaliada | Se violada |
|---|---|---|---|
| 1 | Nome da role é único no sistema | criação e atualização de role | 409 `ROLE_NAME_ALREADY_EXISTS` |
| 2 | `code` de permission é único e só existe se estiver no enum `PermissionCode` | seed/migration (não é criado via API) | constraint de banco (unicidade), não gera erro HTTP; `code` fora do enum nem compila (`RequirePermission` é tipado em `PermissionCode`) |
| 3 | Role não pode ser removida se houver usuário vinculado a ela | remoção de role | 409 `ROLE_IN_USE` |
| 4 | Usuário sem `role_id` não passa em nenhuma checagem de `RequirePermission` | toda rota protegida por `RequirePermission` | 403 `FORBIDDEN` |
| 5 | Usuário autenticado cuja role não tem a permission exigida é bloqueado | toda rota protegida por `RequirePermission` | 403 `FORBIDDEN` |
| 6 | `role_id` informado em `PATCH /users/{id}` precisa existir | atualização de usuário | 404 `ROLE_NOT_FOUND` |
| 7 | Gerenciar roles (`POST`/`PATCH`/`DELETE /roles`, `PUT /roles/{id}/permissions`) exige a permission `roles:manage` | rotas de gestão de role | 403 `FORBIDDEN` (401 se nem autenticado) |
| 8 | O access token JWT carrega `role` (nome ou `null`) e `permissions` (lista de codes) do usuário no momento da emissão, mas `RequirePermission` nunca decide com base nessas claims — sempre consulta a role/permissions atuais no banco | emissão de token (login, refresh) e toda checagem de `RequirePermission` | claim desatualizada não gera erro HTTP; é só a checagem em si que ignora a claim e usa o banco |
| 9 | Toda resposta que serializa um usuário (`UserRead`) traz `role_id` e a role completa (`role`, com `permissions`), não só o id | qualquer resposta com `UserRead` | não se aplica (não é uma regra que "viola" — é o formato do contrato) |

**Regras globais que já se aplicam:** timestamps UTC, paginação máx. 100
(em `GET /roles` e `GET /permissions`), formato único de erro, segredo nunca
sai na resposta.

## 6. Contrato da API

### 6.1 `GET /permissions`

| Campo | Valor |
|---|---|
| **Autenticação** | requer access token |
| **Status de sucesso** | 200 |

**Query:** `limit` (1–100, padrão 20), `offset` (≥ 0)

**Response (200)**

```json
{
  "items": [
    {"id": "3f2b...", "code": "roles:manage", "description": "Gerenciar roles e permissoes"}
  ],
  "total": 2,
  "limit": 20,
  "offset": 0
}
```

**Erros**

| Status | Quando | `code` |
|---|---|---|
| 401 | sem token ou token inválido | `UNAUTHORIZED` |

### 6.2 `POST /roles`

| Campo | Valor |
|---|---|
| **Autenticação** | requer access token + permission `roles:manage` |
| **Status de sucesso** | 201 |

**Request**

```json
{
  "name": "operator",
  "description": "Opera o catalogo, sem gerenciar usuarios"
}
```

| Campo | Tipo | Obrigatório | Regra de formato |
|---|---|---|---|
| `name` | string | sim | 2–100 caracteres, único |
| `description` | string | não | até 500 caracteres |

**Response (201)**

```json
{
  "id": "8a1c...",
  "name": "operator",
  "description": "Opera o catalogo, sem gerenciar usuarios",
  "permissions": [],
  "created_at": "2026-08-11T14:00:00Z",
  "updated_at": "2026-08-11T14:00:00Z"
}
```

**Erros**

| Status | Quando | `code` |
|---|---|---|
| 401 | sem token / token inválido | `UNAUTHORIZED` |
| 403 | autenticado sem a permission `roles:manage` | `FORBIDDEN` |
| 409 | nome de role já existe | `ROLE_NAME_ALREADY_EXISTS` |
| 422 | payload fora do formato | `UNPROCESSABLE_ENTITY` |

### 6.3 `GET /roles` e `GET /roles/{id}`

Autenticado + `roles:manage`, 200. Listagem paginada (RN-GLOBAL-003).
Erros: 401, 403, e no `GET /roles/{id}`: 404 `ROLE_NOT_FOUND`.

### 6.4 `PATCH /roles/{id}`

Autenticado + `roles:manage`, 200. `name`/`description` opcionais.
Erros: 401, 403, 404 `ROLE_NOT_FOUND`, 409 `ROLE_NAME_ALREADY_EXISTS`, 422.

### 6.5 `DELETE /roles/{id}`

Autenticado + `roles:manage`, 204.
Erros: 401, 403, 404 `ROLE_NOT_FOUND`, 409 `ROLE_IN_USE` (regra 3).

### 6.6 `PUT /roles/{id}/permissions`

Substitui, de uma vez, o conjunto de permissions da role.

| Campo | Valor |
|---|---|
| **Autenticação** | requer access token + permission `roles:manage` |
| **Status de sucesso** | 200 |

**Request**

```json
{
  "permission_ids": ["3f2b1c4d-...", "9c0a2b3d-..."]
}
```

**Response (200):** o mesmo formato de `Role` de 6.2, com `permissions`
preenchido.

**Erros**

| Status | Quando | `code` |
|---|---|---|
| 401 | sem token / token inválido | `UNAUTHORIZED` |
| 403 | sem a permission `roles:manage` | `FORBIDDEN` |
| 404 | role não existe, ou algum `permission_id` da lista não existe | `ROLE_NOT_FOUND` / `PERMISSION_NOT_FOUND` |
| 422 | lista vazia ou mal formada | `UNPROCESSABLE_ENTITY` |

### 6.7 `PATCH /users/{id}` (alteração no contrato existente)

Adiciona o campo opcional `role_id` (uuid ou `null`) ao `UserUpdate` já
existente. Continua exigindo apenas `CurrentUserDep` (RN-USERS-004) — quem
pode chamar essa rota não muda nesta tarefa.

`UserRead` (usado por `POST /users`, `GET /users`, `GET /users/{id}`,
`PATCH /users/{id}` e `GET /auth/me`) ganha, além de `role_id`, o campo
`role` com o objeto completo da role (RN-USERS-006):

```json
{
  "id": "3f2b1c4d-...",
  "email": "maria@exemplo.com",
  "role_id": "8a1c...",
  "role": {
    "id": "8a1c...",
    "name": "admin",
    "description": null,
    "permissions": [
      {"id": "...", "code": "roles:manage", "description": "..."},
      {"id": "...", "code": "permissions:read", "description": "..."}
    ],
    "created_at": "2026-08-11T14:00:00Z",
    "updated_at": "2026-08-11T14:00:00Z"
  }
}
```

`role` é `null` quando `role_id` é `null`.

**Erros novos**

| Status | Quando | `code` |
|---|---|---|
| 404 | `role_id` informado não existe | `ROLE_NOT_FOUND` |

### 6.8 `POST /auth/login` e `POST /auth/refresh` (alteração no contrato existente)

O `access_token` retornado passa a ser um JWT com duas claims novas, além
das já existentes (`sub`, `type`, `iat`, `exp`):

| Claim | Tipo | Valor |
|---|---|---|
| `role` | string ou `null` | nome da role do usuário (`null` se `role_id` for `null`) |
| `permissions` | array de string | codes das permissions da role, na forma do `PermissionCode` (`[]` se não tiver role) |

O `refresh_token` **não** ganha essas claims — continua só com `sub`,
`type`, `iat`, `exp` (regra RN-AUTH-003 já garante que ele não é aceito como
access token em nenhuma rota, então carregar role/permissions nele seria
dado morto). `TokenPair` (o corpo da resposta) não muda de formato — as
claims vivem dentro do JWT, não como campo novo do JSON de resposta.

**Erros:** sem mudança em relação ao contrato atual de `/auth/login` e
`/auth/refresh`.

## 7. Estrutura de banco

**Tabela `roles`** · **Migration necessária:** sim

| Coluna | Tipo | Null | Índice | Observação |
|---|---|---|---|---|
| `id` | UUID (PK) | não | PK | vem do `TimestampMixin` |
| `name` | varchar(100) | não | único | regra 1 |
| `description` | varchar(500) | sim | — | |
| `created_at` / `updated_at` | timestamptz | não | — | vem do `TimestampMixin` |

**Tabela `permissions`** · **Migration necessária:** sim

| Coluna | Tipo | Null | Índice | Observação |
|---|---|---|---|---|
| `id` | UUID (PK) | não | PK | vem do `TimestampMixin` |
| `code` | varchar(150) | não | único | formato `recurso:acao`, ex. `roles:manage` |
| `description` | varchar(500) | sim | — | |
| `created_at` / `updated_at` | timestamptz | não | — | vem do `TimestampMixin` |

**Tabela `role_permissions`** (associação N:N, sem model Pydantic próprio)

| Coluna | Tipo | Null | Índice | Observação |
|---|---|---|---|---|
| `role_id` | UUID (FK `roles.id`) | não | PK composta | `ondelete=CASCADE` |
| `permission_id` | UUID (FK `permissions.id`) | não | PK composta | `ondelete=CASCADE` |

**Alteração em `users`**

| Coluna | Tipo | Null | Índice | Observação |
|---|---|---|---|---|
| `role_id` | UUID (FK `roles.id`) | sim | sim | `ondelete=RESTRICT` — reforça a regra 3 no banco, além da checagem no service |

**Relacionamentos:** `users.role_id -> roles.id` (N:1); `role_permissions`
liga `roles` e `permissions` (N:N). Deletar uma role com usuários vinculados
é bloqueado na regra 3 (checagem no service) **e** reforçado no banco com
`ondelete=RESTRICT` — dupla proteção, já que o service pode ter uma corrida
entre o `SELECT` de checagem e o `DELETE`.

**Dados existentes:** `users` já tem linhas em ambientes com dado (dev pelo
menos). `role_id` nasce nullable — sem backfill, usuários existentes ficam
sem role (sem permissão nenhuma) até serem atribuídos manualmente. O
`downgrade` remove a coluna `role_id` de `users` e dropa as três tabelas
novas, nessa ordem: `role_permissions`, `users.role_id`, `permissions`,
`roles`.

## 8. Critérios de aceite

```gherkin
Cenário: cria role com sucesso
  Dado que estou autenticado com a permission "roles:manage"
  E não existe role com o nome "operator"
  Quando envio POST /roles com name = "operator"
  Então recebo status 201
  E o corpo traz permissions = []

Cenário: nome de role duplicado é rejeitado
  Dado que já existe uma role "operator"
  Quando envio POST /roles com name = "operator"
  Então recebo status 409 com code "ROLE_NAME_ALREADY_EXISTS"

Cenário: criar role sem a permission roles:manage é bloqueado
  Dado que estou autenticado, mas minha role não tem "roles:manage"
  Quando envio POST /roles
  Então recebo status 403 com code "FORBIDDEN"

Cenário: criar role sem autenticação é bloqueado
  Dado que não envio token
  Quando envio POST /roles
  Então recebo status 401

Cenário: substitui as permissions de uma role
  Dado que existe a role "operator" e as permissions "products:create" e "products:read"
  Quando envio PUT /roles/{id}/permissions com os dois ids
  Então recebo status 200
  E o corpo traz as duas permissions

Cenário: atribuir permission inexistente é rejeitado
  Dado que existe a role "operator"
  Quando envio PUT /roles/{id}/permissions com um id de permission que não existe
  Então recebo status 404 com code "PERMISSION_NOT_FOUND"

Cenário: remover role em uso é bloqueado
  Dado que a role "operator" está atribuída a um usuário
  Quando envio DELETE /roles/{id}
  Então recebo status 409 com code "ROLE_IN_USE"
  E a role continua no banco

Cenário: remover role sem uso funciona
  Dado que a role "temp" não está atribuída a nenhum usuário
  Quando envio DELETE /roles/{id}
  Então recebo status 204
  E a role não existe mais no banco

Cenário: atribui role a um usuário
  Dado que estou autenticado e existe a role "operator"
  Quando envio PATCH /users/{id} com role_id da role "operator"
  Então recebo status 200
  E o corpo do usuário reflete a nova role

Cenário: atribuir role inexistente ao usuário é rejeitado
  Dado que estou autenticado
  Quando envio PATCH /users/{id} com um role_id que não existe
  Então recebo status 404 com code "ROLE_NOT_FOUND"

Cenário: RequirePermission bloqueia usuário sem a permission
  Dado que estou autenticado com uma role sem a permission PermissionCode.PRODUCTS_CREATE
  Quando chamo uma rota protegida com RequirePermission(PermissionCode.PRODUCTS_CREATE)
  Então recebo status 403 com code "FORBIDDEN"

Cenário: RequirePermission bloqueia usuário sem role nenhuma
  Dado que estou autenticado e meu usuário não tem role_id
  Quando chamo uma rota protegida por RequirePermission(qualquer PermissionCode)
  Então recebo status 403 com code "FORBIDDEN"

Cenário: RequirePermission libera usuário com a permission
  Dado que estou autenticado com uma role que tem a permission PermissionCode.PRODUCTS_CREATE
  Quando chamo uma rota protegida com RequirePermission(PermissionCode.PRODUCTS_CREATE)
  Então a requisição prossegue normalmente (200/201, conforme a rota)

Cenário: catálogo de permissions é listado
  Dado que estou autenticado
  Quando envio GET /permissions
  Então recebo status 200
  E o corpo traz total >= 2 (seed da migration)

Cenário: access token carrega role e permissions do usuário
  Dado que existe o usuário "maria@exemplo.com" com a role "admin"
  Quando envio POST /auth/login com as credenciais de "maria@exemplo.com"
  Então recebo status 200
  E o access_token decodificado traz claim role = "admin"
  E o access_token decodificado traz claim permissions contendo "roles:manage" e "permissions:read"

Cenário: access token de usuário sem role carrega permissions vazio
  Dado que existe um usuário sem role_id
  Quando envio POST /auth/login com as credenciais desse usuário
  Então recebo status 200
  E o access_token decodificado traz claim role = null
  E o access_token decodificado traz claim permissions = []

Cenário: refresh reemite claims atualizadas do token
  Dado que um usuário fez login quando ainda não tinha role
  E depois disso um administrador atribuiu a role "operator" a ele
  Quando envio POST /auth/refresh com o refresh_token emitido antes da atribuição
  Então recebo status 200
  E o novo access_token traz claim role = "operator", refletindo o estado atual
```

## 9. Dúvidas em aberto e decisões

**Dúvidas**

| # | Dúvida | Responsável | Prazo | Status |
|---|---|---|---|---|
| 1 | Usuário deve poder ter mais de uma role (N:N) no futuro, ou 1 role por usuário é suficiente para sempre? | P.O. | antes de iniciar a implementação | aberta |
| 2 | Quem é o "admin" inicial (para não travar sem ninguém com `roles:manage`)? Seed cria a role, mas não atribui a nenhum usuário automaticamente — precisa de um script/comando manual pós-deploy? | Tech Lead | antes de iniciar a implementação | aberta |
| 3 | Número do work item no Azure DevOps | P.O. | antes de entrar em sprint | aberta |

**Decisões tomadas no refinamento**

| Decisão | Por quê | Quem decidiu |
|---|---|---|
| 1 role por usuário (não N:N) | pedido original foi literal: "User pode estar em uma Role"; N:N pode vir depois sem quebrar contrato (troca `role_id` por tabela associativa é migration aditiva) | David (via pedido) |
| Código de permission vive num enum `PermissionCode`, não em string livre | `RequirePermission("prodcuts:create")` (erro de digitação) só quebraria em teste/produção, silenciosamente liberando ou bloqueando acesso; enum dá erro estático e autocomplete, e vira a única fonte de verdade entre seed e router | David (aprovado) |
| Access token carrega `role`/`permissions` como claims | pedido explícito: front/outros serviços conseguem ler o que o usuário pode fazer direto do token, sem chamar `GET /auth/me` | David (aprovado) |
| `UserRead` traz `role` aninhada (com `permissions`), além de `role_id` | pedido explícito: sem isso o cliente precisaria de um `GET /roles/{role_id}` extra toda vez que exibisse um usuário | David (aprovado) |
| `RequirePermission` nunca decide com base nas claims do token, sempre consulta o banco | claim vem do JWT, que fica válido por até `ACCESS_TOKEN_EXPIRE_MINUTES` (30 min por padrão); se a decisão de autorização confiasse nela, revogar uma permission ou trocar a role de um usuário não teria efeito imediato — o usuário continuaria autorizado até o token expirar. Custo é uma consulta a mais por request, aceitável dado o volume esperado | assistente (a validar) |
| `refresh_token` não carrega `role`/`permissions` | ele nunca é usado para autorizar uma rota (RN-AUTH-003), só para gerar um novo access token; adicionar as claims seria dado morto que ainda precisaria ser mantido atualizado | assistente (a validar) |
| Permission é catálogo fixo, sem `POST /permissions` | uma permission só faz sentido junto de um `RequirePermission(code)` real no código; permitir criar via API gera código morto ou, pior, permissions que ninguém aplica | assistente (a validar com Tech Lead) |
| `role_id` nullable em `users`, sem role default automática | usuário sem role fica em fail-closed (sem nenhuma permission) em vez de herdar acesso implícito; mais seguro que uma role "default" com acesso surpresa | assistente (a validar) |
| Delete de role bloqueado por regra 3 + `ondelete=RESTRICT` no banco | dupla proteção contra corrida entre checagem e delete; evita usuário órfão silenciosamente perdendo todo acesso | assistente (a validar) |
| Gestão de roles exige a própria permission `roles:manage` | evita que qualquer usuário autenticado vire admin de si mesmo; custo é o bootstrap (dúvida #2) | assistente (a validar) |

## 10. Definition of Ready

- [x] Seções 1 a 8 preenchidas
- [ ] Nenhuma dúvida bloqueante em aberto — **3 dúvidas abertas, ver seção 9**
- [ ] Contrato da API validado com quem vai consumir
- [ ] Regras de negócio aprovadas pelo P.O.
- [x] Impacto em dados existentes avaliado (seção 7)
- [x] `TODO.md` da pasta revisado

# Regras do módulo `users`

Formato definido em [../README.md](../README.md). Regras globais em [../_global/RULES.md](../_global/RULES.md).

---

### RN-USERS-001 — Senha tem no mínimo 8 caracteres
**Regra:** a senha informada no cadastro ou na troca tem entre 8 e 128 caracteres.
**Quando:** criação de usuário e atualização com campo `password`.
**Se violada:** erro de validação do Pydantic → HTTP 422, code `UNPROCESSABLE_ENTITY`.
**Onde vive:** `app/modules/users/schemas.py` (`UserCreate.password`, `UserUpdate.password`)
**Teste:** `tests/test_users.py::test_senha_curta_retorna_422`

---

### RN-USERS-002 — E-mail é único no sistema
**Regra:** não pode existir mais de um usuário com o mesmo e-mail (comparação já normalizada por RN-GLOBAL-002).
**Quando:** criação de usuário e atualização que troca o e-mail.
**Se violada:** `ConflictError` → HTTP 409, code `EMAIL_ALREADY_EXISTS` em `details`.
**Onde vive:** `app/modules/users/service.py` (`create`, `update`)
**Teste:** `tests/test_users.py::test_email_duplicado_retorna_409`

---

### RN-USERS-003 — Usuário nasce ativo
**Regra:** todo usuário criado começa com `is_active = True`. O cliente não pode escolher esse valor na criação.
**Quando:** criação de usuário (`POST /users` e `POST /auth/register`).
**Se violada:** conta criada sem conseguir autenticar.
**Onde vive:** `app/modules/users/service.py` (`create`)
**Teste:** `tests/test_users.py::test_cria_usuario`

---

### RN-USERS-004 — Listar, ver, alterar e remover usuário exige autenticação
**Regra:** apenas a criação (`POST /users`) e o registro são públicos. As demais rotas de `users` exigem um access token válido.
**Quando:** todas as rotas de `/users` exceto `POST /users`.
**Se violada:** `UnauthorizedError` → HTTP 401.
**Onde vive:** `app/modules/users/router.py` (dependência `CurrentUserDep`)
**Teste:** `tests/test_users.py::test_lista_sem_token_retorna_401`

---

### RN-USERS-005 — `role_id` informado em atualização precisa existir
**Regra:** se `PATCH /users/{id}` informa `role_id` (não `null`), a role precisa existir. `role_id = null` sempre é aceito (remove a role do usuário).
**Quando:** atualização de usuário com o campo `role_id` presente no payload.
**Se violada:** `NotFoundError` → HTTP 404, code `ROLE_NOT_FOUND` em `details`.
**Onde vive:** `app/modules/users/service.py` (`update`)
**Teste:** `tests/test_users.py::test_atribuir_role_inexistente_retorna_404`

---

### RN-USERS-006 — `UserRead` traz a role aninhada, não só o `role_id`
**Regra:** todo `UserRead` (`GET /users`, `GET /users/{id}`, `PATCH /users/{id}`, `POST /users`, `GET /auth/me`) inclui `role_id` **e** `role` (objeto completo, com `name`, `description` e `permissions`), ou `null` se o usuário não tiver role.
**Quando:** toda resposta que serializa um usuário.
**Se violada:** cliente precisaria de um `GET /roles/{role_id}` extra para saber o nome da role e as permissions do usuário.
**Onde vive:** `app/modules/users/schemas.py` (`UserRead.role`)
**Teste:** `tests/test_users.py::test_user_read_traz_role_aninhada`

---

### RN-USERS-007 — Alterar `role_id` exige a permission `users:manage`
**Regra:** `PATCH /users/{id}` so aceita o campo `role_id` no payload (atribuir, trocar ou remover) se o usuario autenticado tiver a permission `PermissionCode.USERS_MANAGE`. Sem essa permission, o campo `role_id` no payload bloqueia a requisicao inteira, mesmo que os outros campos fossem validos. Usuario sem `users:manage` nao pode alterar a propria role nem a de terceiros.
**Quando:** atualizacao de usuario com o campo `role_id` presente no payload (mesmo `null`).
**Se violada:** `ForbiddenError` → HTTP 403.
**Onde vive:** `app/modules/users/router.py` (`RequirePermission(PermissionCode.USERS_MANAGE)`, chamado apenas quando `"role_id" in data.model_fields_set`)
**Teste:** `tests/test_users.py::test_atribuir_role_sem_permission_retorna_403`, `tests/test_users.py::test_usuario_nao_eleva_o_proprio_privilegio`

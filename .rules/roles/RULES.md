# Regras do módulo `roles`

Formato definido em [../README.md](../README.md). Regras globais em [../_global/RULES.md](../_global/RULES.md).

---

### RN-ROLES-001 — Nome da role é único no sistema
**Regra:** não podem existir duas roles com o mesmo nome.
**Quando:** criação de role e atualização que troca o nome.
**Se violada:** `ConflictError` → HTTP 409, code `ROLE_NAME_ALREADY_EXISTS` em `details`.
**Onde vive:** `app/modules/roles/service.py` (`create`, `update`)
**Teste:** `tests/test_roles.py::test_nome_duplicado_retorna_409`

---

### RN-ROLES-002 — Role não pode ser removida se houver usuário vinculado a ela
**Regra:** `DELETE /roles/{id}` é rejeitado enquanto existir ao menos um usuário com aquele `role_id`.
**Quando:** remoção de role.
**Se violada:** `ConflictError` → HTTP 409, code `ROLE_IN_USE` em `details`.
**Onde vive:** `app/modules/roles/service.py` (`delete`); reforçado no banco com `ondelete=RESTRICT` na FK `users.role_id`.
**Teste:** `tests/test_roles.py::test_remove_role_em_uso_retorna_409`

---

### RN-ROLES-003 — Gerenciar roles exige a permission `roles:manage`
**Regra:** criar, listar, buscar, atualizar, remover role e substituir as permissions de uma role exigem a permission `PermissionCode.ROLES_MANAGE`, além de autenticação.
**Quando:** todas as rotas de `/roles`.
**Se violada:** `ForbiddenError` → HTTP 403 (ou 401 se nem autenticado).
**Onde vive:** `app/modules/roles/router.py` (`RequirePermission(PermissionCode.ROLES_MANAGE)`)
**Teste:** `tests/test_roles.py::test_criar_role_sem_permission_retorna_403`

---

### RN-ROLES-004 — Usuário sem role não passa em nenhuma checagem de `RequirePermission`
**Regra:** um usuário autenticado cujo `role_id` é `null` não tem nenhuma permission — fail closed, não existe acesso implícito.
**Quando:** toda rota protegida por `RequirePermission(...)`.
**Se violada:** `ForbiddenError` → HTTP 403.
**Onde vive:** `app/api/deps.py` (`RequirePermission`)
**Teste:** `tests/test_roles.py::test_require_permission_bloqueia_usuario_sem_role`

---

### RN-ROLES-005 — Usuário cuja role não tem a permission exigida é bloqueado
**Regra:** `RequirePermission(code)` verifica se `code.value` está no conjunto de codes da role do usuário autenticado; caso contrário, bloqueia.
**Quando:** toda rota protegida por `RequirePermission(...)`.
**Se violada:** `ForbiddenError` → HTTP 403.
**Onde vive:** `app/api/deps.py` (`RequirePermission`)
**Teste:** `tests/test_roles.py::test_require_permission_bloqueia_usuario_sem_a_permission` e `tests/test_roles.py::test_require_permission_libera_usuario_com_a_permission`

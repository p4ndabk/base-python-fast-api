# Regras do módulo `permissions`

Formato definido em [../README.md](../README.md). Regras globais em [../_global/RULES.md](../_global/RULES.md).

---

### RN-PERMISSIONS-001 — Catálogo de permissions é fixo, definido no enum `PermissionCode`
**Regra:** não existe rota para criar, editar ou remover uma permission. O catálogo nasce de uma migration com seed a partir de `app/core/permissions.py::PermissionCode` e é somente leitura via API.
**Quando:** sempre — não há operação de escrita para este recurso.
**Se violada:** não se aplica (não existe rota que permita violar).
**Onde vive:** `app/core/permissions.py` (enum) + `alembic/versions/0002_cria_tabelas_roles_permissions.py` e migrations de seed subsequentes (uma por permission nova, nunca editando uma ja aplicada)
**Teste:** `tests/test_permissions.py::test_lista_catalogo_de_permissions`, `tests/test_permissions_seed_consistency.py::test_seed_das_migrations_cobre_todo_permissioncode`

---

### RN-PERMISSIONS-002 — Listar permissions exige a permission `permissions:read`
**Regra:** `GET /permissions` exige um access token válido **e** a permission `PermissionCode.PERMISSIONS_READ`.
**Quando:** `GET /permissions`.
**Se violada:** `UnauthorizedError` → HTTP 401 (sem token) ou `ForbiddenError` → HTTP 403 (autenticado sem a permission).
**Onde vive:** `app/modules/permissions/router.py` (`RequirePermission(PermissionCode.PERMISSIONS_READ)`)
**Teste:** `tests/test_permissions.py::test_lista_sem_token_retorna_401`, `tests/test_permissions.py::test_lista_sem_permission_retorna_403`

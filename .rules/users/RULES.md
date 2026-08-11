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

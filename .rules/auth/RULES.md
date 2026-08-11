# Regras do módulo `auth`

Formato definido em [../README.md](../README.md). Regras globais em [../_global/RULES.md](../_global/RULES.md).

---

### RN-AUTH-001 — Senha é armazenada com hash argon2
**Regra:** a senha nunca é persistida em texto puro; o hash usa argon2 via `passlib`.
**Quando:** criação de usuário e troca de senha.
**Se violada:** vazamento total de credenciais em caso de dump do banco.
**Onde vive:** `app/core/security.py` (`hash_password`) usado por `app/modules/users/service.py`
**Teste:** `tests/test_auth.py::test_registra_e_faz_login` (só passa se o hash e a verificação forem coerentes)

---

### RN-AUTH-002 — Falha de login não revela se o e-mail existe
**Regra:** e-mail inexistente e senha errada produzem exatamente a mesma resposta: HTTP 401 com a mensagem `E-mail ou senha invalidos`.
**Quando:** `POST /auth/login`.
**Se violada:** permite enumerar quais e-mails estão cadastrados.
**Onde vive:** `app/modules/auth/service.py` (`login`)
**Teste:** `tests/test_auth.py::test_login_com_senha_errada_retorna_401` e `::test_login_com_email_inexistente_retorna_mesma_mensagem`

---

### RN-AUTH-003 — Access token e refresh token não são intercambiáveis
**Regra:** cada token carrega o campo `type` (`access` ou `refresh`) e só é aceito na operação correspondente.
**Quando:** toda decodificação de token (`get_current_user` e `POST /auth/refresh`).
**Se violada:** `UnauthorizedError` → HTTP 401. Um access token de vida curta poderia ser usado para renovação indefinida.
**Onde vive:** `app/core/security.py` (`decode_token`)
**Teste:** `tests/test_auth.py::test_access_token_nao_serve_como_refresh`

---

### RN-AUTH-004 — Usuário inativo não autentica nem acessa rota protegida
**Regra:** um usuário com `is_active = False` não faz login e não passa em `get_current_user`, mesmo portando um token emitido antes da desativação.
**Quando:** `POST /auth/login`, `POST /auth/refresh` e toda rota protegida.
**Se violada:** `UnauthorizedError` → HTTP 401 com a mensagem `Usuario inativo`.
**Onde vive:** `app/modules/auth/service.py` (`login`, `refresh`) e `app/api/deps.py` (`get_current_user`)
**Teste:** `tests/test_auth.py::test_usuario_inativo_nao_autentica`

---

### RN-AUTH-005 — Access token tem vida curta; refresh token, vida longa
**Regra:** o access token expira em `ACCESS_TOKEN_EXPIRE_MINUTES` (padrão 30 minutos) e o refresh token em `REFRESH_TOKEN_EXPIRE_DAYS` (padrão 7 dias).
**Quando:** emissão de tokens no login e no refresh.
**Se violada:** token expirado → `UnauthorizedError` → HTTP 401.
**Onde vive:** `app/core/security.py` (`create_access_token`, `create_refresh_token`) + `app/core/config.py`
**Teste:** `tests/test_auth.py::test_registra_e_faz_login` (valida `expires_in`)

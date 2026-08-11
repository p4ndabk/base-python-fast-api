# Regras globais

Valem para **todos** os módulos. Ao criar um módulo novo, essas regras já se
aplicam sem precisar repeti-las no arquivo do módulo.

Formato definido em [../README.md](../README.md).

---

### RN-GLOBAL-001 — Timestamps são sempre UTC
**Regra:** `created_at` e `updated_at` são gravados pelo banco em UTC (`TIMESTAMP WITH TIME ZONE`), nunca pelo código da aplicação.
**Quando:** toda escrita em qualquer tabela.
**Se violada:** inconsistência de fuso entre ambientes; não gera erro HTTP.
**Onde vive:** `app/database/base.py` (`TimestampMixin`)
**Teste:** coberto indiretamente por qualquer teste de criação (`tests/test_users.py::test_cria_usuario`)

---

### RN-GLOBAL-002 — E-mail é normalizado antes de persistir
**Regra:** todo e-mail é gravado em lowercase e sem espaços nas pontas.
**Quando:** qualquer entrada que aceite e-mail (criação, atualização, login).
**Se violada:** usuários duplicados que diferem só por caixa; login falha para o usuário legítimo.
**Onde vive:** validators `normalize_email` em `app/modules/users/schemas.py` e `app/modules/auth/schemas.py`
**Teste:** `tests/test_users.py::test_email_normalizado_para_lowercase`

---

### RN-GLOBAL-003 — Listagem é paginada com teto de 100 itens
**Regra:** toda rota de listagem aceita `limit` (1–100, padrão 20) e `offset` (≥ 0), e responde no envelope `{items, total, limit, offset}`.
**Quando:** toda rota `GET` que devolve coleção.
**Se violada:** `422` do Pydantic quando `limit` passa de 100.
**Onde vive:** `app/core/schemas.py` (`PageParams`, `Page`) + o `router.py` de cada módulo
**Teste:** `tests/test_users.py::test_lista_usuarios_paginada`

---

### RN-GLOBAL-004 — Erro da API tem sempre o mesmo formato
**Regra:** toda resposta de erro é `{"error": {"code", "message", "details"}}`. Nenhum módulo cria formato próprio.
**Quando:** qualquer resposta com status ≥ 400.
**Se violada:** o cliente precisa tratar formatos diferentes por rota.
**Onde vive:** `app/main.py` (`_register_exception_handlers`) + `app/core/schemas.py` (`ErrorResponse`)
**Teste:** `tests/test_users.py::test_email_duplicado_retorna_409`

---

### RN-GLOBAL-005 — Segredo nunca sai na resposta
**Regra:** senha, hash de senha e qualquer token de terceiros nunca aparecem em schema de saída.
**Quando:** toda resposta da API.
**Se violada:** vazamento de credenciais.
**Onde vive:** schemas `*Read` de cada módulo
**Teste:** `tests/test_users.py::test_cria_usuario` (verifica ausência de `password` e `hashed_password`)

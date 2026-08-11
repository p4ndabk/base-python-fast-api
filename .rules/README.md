# `.rules/` — Regras de negócio

Esta pasta responde **"o que o sistema deve fazer"**.
Para **"como escrever o código"**, veja [`AGENTS.md`](../AGENTS.md) na raiz.

Toda regra de negócio do sistema mora aqui, com um identificador estável, e é
citada no código e no teste que a implementam. Se a regra não está escrita aqui,
ela **não existe** — não invente regra direto no código.

## Arquivos

| Arquivo | Conteúdo |
|---|---|
| `_global.md` | Regras que valem para todos os módulos |
| `users.md` | Regras do módulo `users` |
| `auth.md` | Regras do módulo `auth` |
| `<modulo>.md` | Um arquivo por módulo novo |

## Identificador

Formato: `RN-<MODULO>-<NNN>` (ex: `RN-USERS-002`).

- A numeração é sequencial **dentro do arquivo** e começa em `001`.
- **IDs nunca são reciclados nem renumerados.** Uma regra que deixa de valer é
  marcada como revogada e o número morre com ela:

  ```markdown
  ### ~~RN-EXEMPLO-003~~ — (revogada em 2026-08-11, substituída por RN-EXEMPLO-009)
  ```

## Formato obrigatório de cada regra

Sempre estes seis campos, nesta ordem — nem mais, nem menos:

```markdown
### RN-USERS-002 — E-mail é único no sistema
**Regra:** não pode existir mais de um usuário com o mesmo e-mail (case-insensitive).
**Quando:** criação e atualização de usuário.
**Se violada:** `ConflictError` → HTTP 409, code `EMAIL_ALREADY_EXISTS`.
**Onde vive:** `app/modules/users/service.py`
**Teste:** `tests/test_users.py::test_email_duplicado_retorna_409`
```

- **Regra** — uma frase, no presente, afirmativa. Sem "deveria", sem "talvez".
- **Quando** — em que operações a regra é avaliada.
- **Se violada** — a exceção de domínio e o status HTTP resultante.
- **Onde vive** — o arquivo que implementa. Quase sempre um `service.py`, porque
  essa é a única camada onde regra de negócio pode morar.
- **Teste** — o teste que prova a regra. Se não existe teste, a regra não está pronta.

## Como amarrar regra ↔ código ↔ teste

Cite o ID como comentário na linha da validação e no docstring do teste:

```python
# app/modules/users/service.py
# RN-USERS-002: e-mail e unico no sistema.
if await self.repository.get_by_email(data.email) is not None:
    raise ConflictError(...)
```

```python
# tests/test_users.py
async def test_email_duplicado_retorna_409(...):
    """RN-USERS-002: e-mail e unico no sistema."""
```

Assim, `grep -r "RN-USERS-002" .` mostra a regra, a implementação e o teste.

## Fluxo ao criar uma regra nova

1. Escreva a regra **aqui primeiro**, com um ID novo.
2. Implemente no `service.py` citando o ID no comentário.
3. Escreva o teste citando o ID no docstring.
4. Preencha o campo **Onde vive** e **Teste** com os caminhos reais.

Nunca comece pelo passo 2.

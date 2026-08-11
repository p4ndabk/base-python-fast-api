---
name: base-tests
description: Como escrever testes neste projeto (pytest async, httpx AsyncClient, fixtures de banco). Use ao testar rotas, regras de negócio ou ao investigar por que um teste falha em tests/test_<modulo>.py.
---

# Camada: tests

Dois estilos, cada um com seu propósito:

| Estilo | O que prova | Custo |
|---|---|---|
| **Teste de rota** (`client`) | o contrato HTTP inteiro: status, corpo, auth | mais lento, bate no banco |
| **Teste de service** (repository fake) | a regra de negócio isolada | rápido, sem banco |

Regra prática: **toda rota** tem teste de rota; **toda regra de negócio complexa**
ganha também um teste de service.

## Arquivos desta pasta
- `example_api.py` — testes de rota de `Product`
- `example_service.py` — testes de service com repository fake
- `template.py.tpl` — esqueleto para copiar

## Fixtures disponíveis (`tests/conftest.py`)
| Fixture | Entrega |
|---|---|
| `db_session` | `AsyncSession` com schema criado e descartado por teste |
| `client` | `AsyncClient` com a sessão de teste injetada no lugar da real |
| `user_payload` | dict pronto para criar usuário |
| `auth_headers` | `{"Authorization": "Bearer ..."}` de um usuário já registrado |

Os testes rodam em SQLite em memória por padrão. Para rodar contra Postgres:
`TEST_DATABASE_URL=postgresql+asyncpg://... uv run pytest`.

## O que MUST estar aqui
- Um teste de sucesso por rota
- Um teste por erro listado no formulário do `base_spec.md` (404, 409, 401, 422…)
- O **ID da regra no docstring** do teste que a cobre: `"""RN-PRODUCTS-001: SKU e unico."""`
- Nome no formato `test_<acao>_<resultado_esperado>`

## O que NEVER pode aparecer
- `@pytest.mark.asyncio` — o `asyncio_mode = "auto"` já cuida disso
- Teste que depende da ordem de execução ou de dado deixado por outro teste
- `time.sleep()`
- Assert só no status code quando o corpo também importa

## Erros mais comuns
1. Esquecer `await` na chamada do `client` → o assert roda sobre uma corrotina.
2. Contar errado o `total` na paginação: a fixture `auth_headers` **já criou um usuário**.
3. Testar mensagem de erro literal onde o código não garante o texto — prefira `error.code`.
4. Criar o próprio engine em vez de usar a fixture `db_session`.
5. Esperar 400 onde o Pydantic devolve 422 (validação de schema é sempre 422).

## Comandos
```bash
uv run pytest                                   # tudo
uv run pytest tests/test_products.py -v         # um arquivo
uv run pytest -k "duplicado"                    # por nome
uv run pytest -x                                # para no primeiro erro
```

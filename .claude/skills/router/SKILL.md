---
name: router
description: Como escrever a camada de router (declaração das rotas FastAPI) deste projeto. Use ao criar ou alterar endpoints, status codes, response_model, autenticação ou parâmetros de query em app/modules/<modulo>/router.py.
---

# Camada: router

`← HTTP | → controller.py`

O router é **só a declaração do contrato HTTP**. Deve ser legível como
documentação: quem abre o arquivo entende a API sem ler mais nada.

## Leitura obrigatória antes de escrever
[`.claude/base_spec.md`](../../base_spec.md) — o rito completo de criação de
rota, incluindo o formulário que você deve preencher antes de codar.

## Arquivos desta pasta
- `example.py` — o router de `Product`, completo e comentado
- `template.py.tpl` — o mesmo arquivo com `{{Entity}}` para copiar

## O que MUST estar aqui
- `router = APIRouter(prefix="/products", tags=["products"])`
- Toda função de rota é `async def` e delega ao controller **em uma linha**
- `response_model=` e `status_code=` declarados em toda rota
- `responses={404: {"model": ErrorResponse, ...}}` para cada erro possível
- `SessionDep` para a sessão e `CurrentUserDep` para rota autenticada
- `summary=` — vira o título da rota no `/docs`

## O que NEVER pode aparecer
- `if`, `try/except`, laço — qualquer lógica
- `select()`, sessão usada diretamente
- Ler o header `Authorization` na mão — use `CurrentUserDep`
- `def` síncrono
- Rota sem `response_model` (exceto 204)

## Contrato fixo
Path no plural, kebab-case; a ação vem do método HTTP.

| Operação | Rota | Status |
|---|---|---|
| Listar | `GET /products` | 200 |
| Buscar | `GET /products/{id}` | 200 |
| Criar | `POST /products` | 201 |
| Atualizar | `PATCH /products/{id}` | 200 |
| Remover | `DELETE /products/{id}` | 204 |

Proibido: `/products/create-product`, `/getProducts`, `/product`.

## Erros mais comuns
1. **Esquecer de registrar o router em `app/api/v1.py`** — a rota simplesmente não existe. Erro nº 1.
2. Ordem das rotas: `/products/featured` declarada **depois** de `/products/{id}` nunca é alcançada — declare as rotas literais antes das paramétricas.
3. Esquecer `status_code=201` no POST (fica 200).
4. Devolver corpo num 204.
5. Colocar validação no router porque "é rapidinho".
6. Não declarar `responses={...}`, deixando o `/docs` incompleto.

## Depois de mexer aqui
1. Registre o router em `app/api/v1.py`
2. Vá para a skill `tests`

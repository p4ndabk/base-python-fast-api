# 1234 — Cadastro de produtos

> **Exemplo de referência.** Esta spec é fictícia e existe para mostrar o nível
> de detalhe esperado. Copie `docs/specs/_template/` para criar a sua.

## 1. Identificação

| Campo | Valor |
|---|---|
| **Work item (Azure DevOps)** | #1234 — https://dev.azure.com/org/proj/_workitems/edit/1234 |
| **Tipo** | User Story |
| **Épico / Feature pai** | #1200 — Catálogo |
| **Módulo afetado** | `app/modules/products` (novo) |
| **P.O.** | Ana Ribeiro |
| **Tech Lead** | Carlos Menezes |
| **Data do refinamento** | 2026-08-05 |
| **Depende de** | nada |

## 2. Contexto e objetivo

**Problema:** o catálogo é mantido hoje numa planilha compartilhada. Não há
controle de quem alterou o quê, dois vendedores já cadastraram o mesmo item com
códigos diferentes, e o e-commerce precisa consultar preço por API.

**Objetivo:** ter os produtos no banco, com código único e histórico de
alteração, expostos por uma API que o e-commerce consome.

**Quem usa:** operador de catálogo (cadastra pelo backoffice) e o e-commerce
(lê o catálogo).

## 3. Escopo — o que entra

- [ ] Criar produto com nome, SKU, preço e descrição opcional
- [ ] Listar produtos com paginação
- [ ] Buscar produto por id
- [ ] Atualizar produto (parcial)
- [ ] Desativar produto (sem apagar do banco)

## 4. Fora de escopo

- Categorias de produto — entra na #1240
- Upload de imagem — depende da definição de storage, ainda não decidida
- Controle de estoque — outro domínio, fora do catálogo
- Importar a planilha atual — será uma tarefa de migração de dados (#1238)
- Preço por região ou tabela promocional

## 5. Regras de negócio

| # | Regra | Quando é avaliada | Se violada |
|---|---|---|---|
| 1 | SKU é único no sistema | criação e atualização | 409 `SKU_ALREADY_EXISTS` |
| 2 | Preço é sempre maior que zero | criação e atualização | 422 (validação de schema) |
| 3 | Produto nasce ativo | criação | — (o cliente não escolhe) |
| 4 | Produto já inativo não pode ser desativado de novo | desativação | 400 `VALIDATION_ERROR` |
| 5 | Produto não é apagado, apenas desativado | remoção | — |

**Regras globais que já se aplicam:** timestamps UTC, paginação máx. 100,
formato único de erro.

## 6. Contrato da API

### 6.1 `POST /products`

| Campo | Valor |
|---|---|
| **Autenticação** | requer access token |
| **Status de sucesso** | 201 |

**Request**

```json
{
  "name": "Teclado mecanico ABNT2",
  "sku": "TEC-001",
  "price": "199.90",
  "description": "Switch marrom, 87 teclas"
}
```

| Campo | Tipo | Obrigatório | Regra de formato |
|---|---|---|---|
| `name` | string | sim | 2–255 caracteres |
| `sku` | string | sim | 1–64 caracteres, normalizado para maiúsculas |
| `price` | decimal (string) | sim | > 0, duas casas |
| `description` | string | não | até 2000 caracteres |

**Response (201)**

```json
{
  "id": "3f2b1c4d-5e6f-4a7b-8c9d-0e1f2a3b4c5d",
  "name": "Teclado mecanico ABNT2",
  "sku": "TEC-001",
  "price": "199.90",
  "description": "Switch marrom, 87 teclas",
  "is_active": true,
  "created_at": "2026-08-05T14:30:00Z",
  "updated_at": "2026-08-05T14:30:00Z"
}
```

**Erros**

| Status | Quando | `code` |
|---|---|---|
| 401 | sem token ou token inválido | `UNAUTHORIZED` |
| 409 | SKU já cadastrado | `SKU_ALREADY_EXISTS` |
| 422 | preço ≤ 0, nome curto, campo faltando | `UNPROCESSABLE_ENTITY` |

### 6.2 `GET /products`

| Campo | Valor |
|---|---|
| **Autenticação** | pública |
| **Status de sucesso** | 200 |

**Query:** `limit` (1–100, padrão 20), `offset` (≥ 0), `only_active` (bool, padrão `false`)

**Response (200)**

```json
{
  "items": [{ "id": "...", "name": "...", "sku": "TEC-001", "price": "199.90", "is_active": true }],
  "total": 42,
  "limit": 20,
  "offset": 0
}
```

### 6.3 `PATCH /products/{id}`

Autenticado, 200. Todos os campos opcionais. Erros: 401, 404 `NOT_FOUND`,
409 `SKU_ALREADY_EXISTS`, 422.

### 6.4 `DELETE /products/{id}`

Autenticado, 204. Desativa (`is_active = false`), não apaga.
Erros: 401, 404 `NOT_FOUND`, 400 `VALIDATION_ERROR` se já estiver inativo.

## 7. Estrutura de banco

**Tabela:** `products` · **Migration necessária:** sim

| Coluna | Tipo | Null | Índice | Observação |
|---|---|---|---|---|
| `id` | UUID (PK) | não | PK | vem do `TimestampMixin` |
| `name` | varchar(255) | não | sim | busca por nome no futuro |
| `sku` | varchar(64) | não | único | unicidade também no banco (regra 1) |
| `price` | numeric(10,2) | não | — | `Numeric`, nunca `Float` |
| `description` | text | sim | — | |
| `is_active` | boolean | não | — | default `true` |
| `created_at` | timestamptz | não | — | vem do `TimestampMixin` |
| `updated_at` | timestamptz | não | — | vem do `TimestampMixin` |

**Relacionamentos:** nenhum nesta tarefa. A FK para `categories` entra na #1240.

**Dados existentes:** tabela nova, sem backfill. A carga da planilha é a #1238.

## 8. Critérios de aceite

```gherkin
Cenário: cadastro de produto com dados válidos
  Dado que estou autenticado
  E não existe produto com o SKU "TEC-001"
  Quando envio POST /products com name, sku, price válidos
  Então recebo status 201
  E o corpo traz o id gerado e is_active = true

Cenário: SKU duplicado é rejeitado
  Dado que já existe um produto com o SKU "TEC-001"
  Quando envio POST /products com o mesmo SKU
  Então recebo status 409 com code "SKU_ALREADY_EXISTS"
  E nenhum produto novo é criado

Cenário: preço zero é rejeitado
  Dado que estou autenticado
  Quando envio POST /products com price = "0"
  Então recebo status 422

Cenário: cadastro sem autenticação é bloqueado
  Dado que não envio token
  Quando envio POST /products
  Então recebo status 401

Cenário: listagem é pública e paginada
  Dado que existem 42 produtos cadastrados
  Quando envio GET /products?limit=20&offset=0 sem token
  Então recebo status 200
  E o corpo traz 20 itens e total = 42

Cenário: produto inexistente
  Dado que estou autenticado
  Quando envio GET /products/{id que não existe}
  Então recebo status 404 com code "NOT_FOUND"

Cenário: desativar produto não apaga o registro
  Dado que existe um produto ativo
  Quando envio DELETE /products/{id}
  Então recebo status 204
  E o produto continua no banco com is_active = false

Cenário: desativar produto já inativo
  Dado que existe um produto com is_active = false
  Quando envio DELETE /products/{id}
  Então recebo status 400
```

## 9. Dúvidas em aberto e decisões

**Dúvidas**

| # | Dúvida | Responsável | Prazo | Status |
|---|---|---|---|---|
| 1 | SKU aceita letras minúsculas? | Ana (P.O.) | 2026-08-04 | respondida: normaliza para maiúsculas |
| 2 | Listagem é pública mesmo? | Ana (P.O.) | 2026-08-04 | respondida: sim, o e-commerce consome sem login |

**Decisões tomadas no refinamento**

| Decisão | Por quê | Quem decidiu |
|---|---|---|
| `DELETE` desativa em vez de apagar | pedido já emitido referencia o produto; apagar quebraria o histórico | Carlos (TL) |
| `price` como `Numeric(10,2)`, não `Float` | `Float` perde centavos em operação financeira | Carlos (TL) |
| Sem categoria nesta tarefa | a modelagem de categoria ainda está em discussão; travaria a entrega | Ana + Carlos |
| Listagem pública | o e-commerce consulta o catálogo sem sessão de usuário | Ana (P.O.) |

## 10. Definition of Ready

- [x] Seções 1 a 8 preenchidas
- [x] Nenhuma dúvida bloqueante em aberto
- [x] Contrato validado com o time do e-commerce
- [x] Regras de negócio aprovadas pelo P.O.
- [x] Impacto em dados existentes avaliado (tabela nova)
- [x] `TODO.md` revisado

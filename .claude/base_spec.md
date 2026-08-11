# base_spec.md — como nasce uma rota neste projeto

**Leitura obrigatória antes de criar ou alterar qualquer rota.**

Este documento é deliberadamente burocrático. O rito é chato de propósito: o
custo de segui-lo é muito menor que o de revisar código improvisado. Se você
achar que uma etapa é desnecessária neste caso específico, você está errado —
faça a etapa.

**MUST** = obrigatório. **NEVER** = proibido. Não há meio-termo.

---

## Etapa 1 — Preencher o formulário (antes de escrever a primeira linha)

Você **MUST** preencher este formulário por completo antes de tocar em qualquer
arquivo. Cole-o preenchido na sua resposta antes de começar a implementar.

```
## Especificação da rota

Método + path .........: POST /products
Módulo ................: products
Autenticação ..........: [ ] pública  [x] requer access token
Schema de entrada .....: ProductCreate {name: str, price: Decimal, sku: str}
Schema de saída .......: ProductRead
Status de sucesso .....: 201
Erros possíveis .......: 409 SKU já cadastrado (ConflictError)
                         422 entrada inválida (Pydantic)
                         401 sem token
Regras de negócio .....: RN-PRODUCTS-001, RN-PRODUCTS-002, RN-GLOBAL-002
Efeito no banco .......: INSERT em products; migration necessária: SIM
Paginação .............: N/A (só em listagem)
```

Regras desta etapa:

- Se **qualquer** campo não puder ser preenchido com certeza, você **MUST**
  parar e perguntar ao usuário. **NEVER** adivinhe um contrato de API.
- Se a rota aplica uma regra de negócio que ainda **não existe** em `.rules/`,
  você **MUST** escrever a regra lá primeiro (com ID novo) e só então implementar.
- **NEVER** comece pelo `router.py`.

---

## Etapa 2 — Implementar de baixo para cima, nesta ordem

A ordem não é negociável. Escrever o router primeiro leva a inventar contratos
que a camada de baixo não sustenta.

### 2.1 `schemas.py`
- **MUST** ter `{Entity}Create`, `{Entity}Update` (todos os campos opcionais) e `{Entity}Read`.
- **MUST** ter `model_config = ConfigDict(from_attributes=True)` no `Read`.
- **NEVER** importar SQLAlchemy aqui.
- **NEVER** expor senha, hash ou segredo no `Read` (RN-GLOBAL-005).

### 2.2 `models.py` (só se a rota mexe em tabela)
- **MUST** herdar de `Base, TimestampMixin`.
- **MUST** usar `Mapped[...]` / `mapped_column(...)`.
- **NEVER** colocar regra de negócio ou Pydantic aqui.

### 2.3 `repository.py`
- **MUST** receber `AsyncSession` no `__init__`.
- **MUST** ser o **único** lugar do módulo com `select()` / `session.execute()`.
- **MUST** usar `flush()` após `add()`.
- **NEVER** chamar `commit()`.
- **NEVER** levantar erro de domínio (devolva `None` e deixe o service decidir).

### 2.4 `service.py`
- **MUST** receber o repository no `__init__`.
- **MUST** implementar cada regra do formulário citando o ID em comentário: `# RN-PRODUCTS-001: ...`.
- **MUST** chamar `commit()` ao final da operação de escrita.
- **MUST** chamar `repository.refresh(obj)` depois de um UPDATE.
- **NEVER** importar `fastapi`, `HTTPException` ou `Request`.
- **NEVER** montar query.

### 2.5 `controller.py`
- **MUST** montar o service a partir da `AsyncSession` recebida.
- **MUST** converter o model para o schema de saída com `{Entity}Read.model_validate(obj)`.
- **NEVER** conter `if` de regra de negócio.

### 2.6 `router.py`
- **MUST** declarar `APIRouter(prefix="/products", tags=["products"])`.
- **MUST** declarar `response_model` e `status_code` em toda rota.
- **MUST** declarar os erros no `responses={...}` usando `ErrorResponse`.
- **MUST** ser `async def` e delegar ao controller em uma linha.
- **NEVER** conter `if`, `try` ou query.

### 2.7 Registro
- **MUST** incluir o router em `app/api/v1.py`.
- **MUST** importar o `models` do módulo em `alembic/env.py` (senão o autogenerate ignora a tabela).

### 2.8 `tests/test_<modulo>.py`
- **MUST** existir um teste de sucesso.
- **MUST** existir um teste para **cada** erro listado no formulário.
- **MUST** citar o ID da regra no docstring do teste que a cobre.

### 2.9 Migration (se mexeu em tabela)
- **MUST** rodar `uv run alembic revision --autogenerate -m "descricao"` e **revisar o arquivo gerado** antes de aplicar.
- **MUST** conferir que `downgrade()` desfaz o que `upgrade()` faz.
- **NEVER** editar uma migration já aplicada em outro ambiente; crie uma nova.

---

## Etapa 3 — Contrato de rota (padrão fixo da API)

### Path
- Substantivo no **plural**, kebab-case: `/products`, `/order-items`.
- A ação vem do **método HTTP**, nunca do path.
- **NEVER**: `/products/create-product`, `/getProducts`, `/product`.

| Operação | Método + path | Status |
|---|---|---|
| Listar | `GET /products` | 200 |
| Buscar por id | `GET /products/{id}` | 200 |
| Criar | `POST /products` | 201 |
| Atualizar parcial | `PATCH /products/{id}` | 200 |
| Substituir | `PUT /products/{id}` | 200 |
| Remover | `DELETE /products/{id}` | 204 (sem corpo) |

### Status codes
| Código | Quando |
|---|---|
| 200 | leitura ou atualização bem-sucedida |
| 201 | recurso criado |
| 204 | removido, sem corpo de resposta |
| 400 | regra de negócio violada (`DomainValidationError`) |
| 401 | sem token, token inválido ou expirado |
| 403 | autenticado, mas sem permissão |
| 404 | recurso não existe |
| 409 | conflito com o estado atual (duplicidade) |
| 422 | corpo não passou na validação do Pydantic |
| 503 | dependência externa fora (banco, fila) |

### Formato de erro (único em toda a API)
```json
{"error": {"code": "CONFLICT", "message": "Ja existe um usuario com este e-mail", "details": {"field": "email"}}}
```

### Paginação (única em toda a API)
Query: `limit` (1–100, padrão 20) e `offset` (≥ 0).
Resposta: `{"items": [...], "total": 42, "limit": 20, "offset": 0}` via `Page[{Entity}Read]`.

---

## Etapa 4 — Regras de assinatura

- Toda função de rota **MUST** ser `async def`.
- `response_model` **MUST** estar declarado (exceto em 204).
- A sessão **MUST** entrar pelo router via `SessionDep` e descer por parâmetro.
- `Request` **NEVER** aparece fora do `router.py`.
- Autenticação **MUST** ser declarada com `CurrentUserDep` — **NEVER** leia o header `Authorization` na mão.

---

## Etapa 5 — Definition of Done

A rota só está pronta quando **todos** os itens estiverem marcados:

- [ ] O formulário da Etapa 1 foi preenchido e está coerente com o código final
- [ ] As camadas foram criadas na ordem da Etapa 2
- [ ] A rota aparece em `/docs` com o schema e os erros corretos
- [ ] Existe teste de sucesso
- [ ] Existe teste para **cada** erro listado no formulário
- [ ] Toda regra citada no formulário está em `.rules/`, implementada no service e coberta por um teste que cita o mesmo ID
- [ ] `uv run pytest` verde
- [ ] `uv run ruff check .` limpo
- [ ] Migration gerada, revisada e aplicada (se houve mudança de tabela)
- [ ] Router registrado em `app/api/v1.py` e model importado em `alembic/env.py`
- [ ] Nenhum anti-padrão da seção 6 do [`AGENTS.md`](../AGENTS.md) no diff

---

## Exemplo completo — `POST /products`

### Formulário preenchido
```
Método + path .........: POST /products
Módulo ................: products
Autenticação ..........: requer access token
Schema de entrada .....: ProductCreate {name: str, sku: str, price: Decimal}
Schema de saída .......: ProductRead
Status de sucesso .....: 201
Erros possíveis .......: 409 SKU duplicado / 422 entrada inválida / 401 sem token
Regras de negócio .....: RN-PRODUCTS-001 (SKU único), RN-PRODUCTS-002 (preço > 0)
Efeito no banco .......: INSERT em products; migration: SIM
```

### Regra escrita antes do código, em `.rules/products.md`
```markdown
### RN-PRODUCTS-001 — SKU é único
**Regra:** não existem dois produtos com o mesmo SKU.
**Quando:** criação e atualização de produto.
**Se violada:** `ConflictError` → HTTP 409, code `SKU_ALREADY_EXISTS`.
**Onde vive:** `app/modules/products/service.py`
**Teste:** `tests/test_products.py::test_sku_duplicado_retorna_409`
```

### As camadas (resumo — o código completo está em cada skill)
```python
# schemas.py
class ProductCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    sku: str = Field(..., min_length=1, max_length=64)
    price: Decimal = Field(..., gt=0)  # RN-PRODUCTS-002


# repository.py
async def get_by_sku(self, sku: str) -> ProductModel | None:
    result = await self.session.execute(select(ProductModel).where(ProductModel.sku == sku))
    return result.scalars().first()


# service.py
async def create(self, data: ProductCreate) -> ProductModel:
    # RN-PRODUCTS-001: SKU e unico.
    if await self.repository.get_by_sku(data.sku) is not None:
        raise ConflictError(
            "Ja existe produto com este SKU", details={"field": "sku", "code": "SKU_ALREADY_EXISTS"}
        )
    product = ProductModel(**data.model_dump())
    await self.repository.add(product)
    await self.repository.session.commit()
    return product


# controller.py
async def create(self, data: ProductCreate) -> ProductRead:
    return ProductRead.model_validate(await self.service.create(data))


# router.py
@router.post(
    "",
    response_model=ProductRead,
    status_code=status.HTTP_201_CREATED,
    responses={409: {"model": ErrorResponse, "description": "SKU ja cadastrado"}},
)
async def create_product(
    data: ProductCreate, session: SessionDep, _: CurrentUserDep
) -> ProductRead:
    return await ProductController(session).create(data)
```

### Testes
```python
async def test_cria_produto(client, auth_headers):
    response = await client.post("/products", json={...}, headers=auth_headers)
    assert response.status_code == 201


async def test_sku_duplicado_retorna_409(client, auth_headers):
    """RN-PRODUCTS-001: SKU e unico."""
    await client.post("/products", json={...}, headers=auth_headers)
    response = await client.post("/products", json={...}, headers=auth_headers)
    assert response.status_code == 409
```

O módulo `users` no repositório é este mesmo padrão, implementado por completo —
use-o como referência viva quando o exemplo acima não bastar.

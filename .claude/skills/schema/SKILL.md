---
name: schema
description: Como escrever a camada de schema (contratos Pydantic de entrada e saída) deste projeto. Use ao definir o corpo de request/response de uma rota, validação de campo ou paginação em app/modules/<modulo>/schemas.py.
---

# Camada: schema

`← router / controller | → nada (é um contrato, não chama ninguém)`

Schema é o **contrato da API**. É o que aparece no `/docs` e o que o cliente vê.

## Arquivos desta pasta
- `example.py` — os schemas de `Product`, completos e comentados
- `template.py.tpl` — o mesmo arquivo com `{{Entity}}` para copiar

## O que MUST estar aqui
- `{Entity}Create` — o que o cliente envia para criar
- `{Entity}Update` — **todos os campos opcionais** (`| None = None`), porque `PATCH` é parcial
- `{Entity}Read` — o que a API devolve, com `model_config = ConfigDict(from_attributes=True)`
- Constraints declarativas: `Field(..., min_length=, max_length=, gt=, ge=)`
- `examples=[...]` nos campos principais — vira exemplo no Swagger

## O que NEVER pode aparecer
- Importar SQLAlchemy ou o `Model`
- Acesso ao banco
- Senha, hash ou segredo em schema de saída (RN-GLOBAL-005)
- Regra que depende de **outro registro** ("SKU já existe") — isso é `service.py`, não dá para validar sem banco

## Validação: o que vai aqui e o que vai no service

| Tipo de validação | Onde |
|---|---|
| formato, tamanho, faixa numérica, obrigatoriedade | **schema** (Pydantic → 422) |
| normalização (lowercase, trim) | **schema** (`field_validator`) |
| coerência entre campos do mesmo payload | **schema** (`model_validator`) |
| qualquer coisa que precise consultar o banco | **service** (erro de domínio → 400/409) |

## Erros mais comuns
1. `{Entity}Update` com campos obrigatórios — quebra o `PATCH` parcial.
2. Esquecer `ConfigDict(from_attributes=True)` no `Read` → `model_validate(model)` falha.
3. Expor `hashed_password` por herdar do schema errado.
4. Tentar validar unicidade no schema (impossível: não há sessão de banco aqui).
5. Usar `float` para dinheiro — use `Decimal`.

## Depois de mexer aqui
Vá para a skill `repository`.

"""EXEMPLO da camada SCHEMA — `app/modules/products/schemas.py`.

Referência viva no repositório: `app/modules/users/schemas.py`.
"""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ProductBase(BaseModel):
    """Campos comuns entre entrada e saida. Evita repeticao."""

    # ok constraints declarativas: viram validacao 422 e documentacao no /docs
    name: str = Field(..., min_length=2, max_length=255, examples=["Teclado mecanico"])
    sku: str = Field(..., min_length=1, max_length=64, examples=["TEC-001"])

    # ok dinheiro e Decimal com gt=0 (RN-PRODUCTS-002 vira constraint declarativa)
    price: Decimal = Field(..., gt=0, examples=["199.90"])

    description: str | None = Field(default=None, max_length=2000)

    @field_validator("sku")
    @classmethod
    def normalize_sku(cls, value: str) -> str:
        # ok normalizacao pertence ao schema: nao depende do banco
        return value.strip().upper()

    @model_validator(mode="after")
    def nome_diferente_do_sku(self):
        # ok coerencia entre campos do MESMO payload tambem e schema
        if self.name.strip().upper() == self.sku:
            raise ValueError("name e sku nao podem ser iguais")
        return self


class ProductCreate(ProductBase):
    """O que o cliente envia no POST."""

    # no NUNCA valide aqui "SKU ja existe": isso exige consultar o banco.
    #    Essa regra vive no service (RN-PRODUCTS-001) e devolve 409, nao 422.


class ProductUpdate(BaseModel):
    """O que o cliente envia no PATCH.

    ok TODOS os campos opcionais - PATCH e atualizacao parcial.
    no NUNCA herde de ProductCreate aqui: os campos obrigatorios viriam junto.
    """

    name: str | None = Field(default=None, min_length=2, max_length=255)
    sku: str | None = Field(default=None, min_length=1, max_length=64)
    price: Decimal | None = Field(default=None, gt=0)
    description: str | None = Field(default=None, max_length=2000)
    is_active: bool | None = None


class ProductRead(ProductBase):
    """O que a API devolve."""

    # ok obrigatorio para `ProductRead.model_validate(product_model)` funcionar
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    # no NUNCA adicione aqui: hashed_password, tokens, chaves de API (RN-GLOBAL-005)


# Para listagem, use o envelope compartilhado - nao crie um proprio:
#   from app.core.schemas import Page
#   Page[ProductRead]

"""Contratos de entrada/saida do modulo {{entities}}.

Camada SCHEMA: so Pydantic. Nenhum SQLAlchemy, nenhum acesso a banco.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class {{Entity}}Base(BaseModel):
    name: str = Field(..., min_length=2, max_length=255, examples=["Nome do {{entity}}"])


class {{Entity}}Create({{Entity}}Base):
    """O que o cliente envia no POST."""


class {{Entity}}Update(BaseModel):
    """O que o cliente envia no PATCH - todos os campos opcionais."""

    name: str | None = Field(default=None, min_length=2, max_length=255)
    is_active: bool | None = None


class {{Entity}}Read({{Entity}}Base):
    """O que a API devolve."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

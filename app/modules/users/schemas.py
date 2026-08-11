"""Contratos de entrada/saida do modulo users.

Regra: `hashed_password` NUNCA aparece em um schema de saida.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserBase(BaseModel):
    email: EmailStr = Field(..., examples=["maria@exemplo.com"])
    full_name: str = Field(..., min_length=2, max_length=255, examples=["Maria Silva"])

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        # RN-GLOBAL-002: e-mail e sempre normalizado para lowercase antes de persistir.
        return value.strip().lower()


class UserCreate(UserBase):
    # RN-USERS-001: senha tem no minimo 8 caracteres.
    password: str = Field(..., min_length=8, max_length=128, examples=["senha-super-secreta"])


class UserUpdate(BaseModel):
    """Atualizacao parcial: todos os campos sao opcionais."""

    email: EmailStr | None = None
    full_name: str | None = Field(default=None, min_length=2, max_length=255)
    password: str | None = Field(default=None, min_length=8, max_length=128)
    is_active: bool | None = None

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str | None) -> str | None:
        return value.strip().lower() if value else value


class UserRead(UserBase):
    """Representacao publica do usuario.

    RN-GLOBAL-005: `hashed_password` e `password` NUNCA entram aqui.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

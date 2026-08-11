"""Contratos de entrada/saida do modulo roles."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.modules.permissions.schemas import PermissionRead


class RoleBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, examples=["operator"])
    description: str | None = Field(default=None, max_length=500)


class RoleCreate(RoleBase):
    pass


class RoleUpdate(BaseModel):
    """Atualizacao parcial: todos os campos sao opcionais."""

    name: str | None = Field(default=None, min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=500)


class RoleRead(RoleBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    permissions: list[PermissionRead]
    created_at: datetime
    updated_at: datetime


class RolePermissionsUpdate(BaseModel):
    """Substitui de uma vez o conjunto de permissions da role.

    Lista vazia e valida: PUT substitui o conjunto inteiro, e uma role sem
    nenhuma permission e um estado legitimo (RN-ROLES-006).
    """

    permission_ids: list[uuid.UUID] = Field(default_factory=list)

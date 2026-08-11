"""Contratos de saida do modulo permissions.

Nao ha schema de entrada: o catalogo e somente leitura (RN-PERMISSIONS-001).
"""

import uuid

from pydantic import BaseModel, ConfigDict


class PermissionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    description: str | None

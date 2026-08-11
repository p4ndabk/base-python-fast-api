"""Regras de negocio de permissions.

Modulo somente leitura (RN-PERMISSIONS-001): nao ha create/update/delete.
"""

from app.modules.permissions.models import PermissionModel
from app.modules.permissions.repository import PermissionRepository


class PermissionService:
    def __init__(self, repository: PermissionRepository) -> None:
        self.repository = repository

    async def list(self, *, limit: int, offset: int) -> tuple[list[PermissionModel], int]:
        permissions = await self.repository.list(limit=limit, offset=offset)
        total = await self.repository.count()
        return permissions, total

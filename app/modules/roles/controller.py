"""Orquestracao do modulo roles.

Camada CONTROLLER: monta o service, chama o metodo certo e converte model ->
schema de saida. Nao contem regra de negocio nem query.
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.schemas import Page
from app.modules.permissions.repository import PermissionRepository
from app.modules.roles.repository import RoleRepository
from app.modules.roles.schemas import RoleCreate, RolePermissionsUpdate, RoleRead, RoleUpdate
from app.modules.roles.service import RoleService


class RoleController:
    def __init__(self, session: AsyncSession) -> None:
        self.service = RoleService(RoleRepository(session), PermissionRepository(session))

    async def create(self, data: RoleCreate) -> RoleRead:
        role = await self.service.create(data)
        return RoleRead.model_validate(role)

    async def get(self, role_id: uuid.UUID) -> RoleRead:
        role = await self.service.get(role_id)
        return RoleRead.model_validate(role)

    async def list(self, *, limit: int, offset: int) -> Page[RoleRead]:
        roles, total = await self.service.list(limit=limit, offset=offset)
        return Page[RoleRead](
            items=[RoleRead.model_validate(role) for role in roles],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def update(self, role_id: uuid.UUID, data: RoleUpdate) -> RoleRead:
        role = await self.service.update(role_id, data)
        return RoleRead.model_validate(role)

    async def delete(self, role_id: uuid.UUID) -> None:
        await self.service.delete(role_id)

    async def set_permissions(self, role_id: uuid.UUID, data: RolePermissionsUpdate) -> RoleRead:
        role = await self.service.set_permissions(role_id, data)
        return RoleRead.model_validate(role)

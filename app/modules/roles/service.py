"""Regras de negocio de roles.

Camada SERVICE: onde as regras de `.rules/roles/RULES.md` sao implementadas.

Proibido aqui: HTTPException, Request, `select()`. Use erros de dominio.
"""

import uuid

from app.core.exceptions import ConflictError, NotFoundError
from app.modules.permissions.repository import PermissionRepository
from app.modules.roles.models import RoleModel
from app.modules.roles.repository import RoleRepository
from app.modules.roles.schemas import RoleCreate, RolePermissionsUpdate, RoleUpdate
from app.modules.users.repository import UserRepository


class RoleService:
    def __init__(
        self,
        repository: RoleRepository,
        permission_repository: PermissionRepository,
        user_repository: UserRepository,
    ) -> None:
        self.repository = repository
        self.permission_repository = permission_repository
        self.user_repository = user_repository

    async def create(self, data: RoleCreate) -> RoleModel:
        # RN-ROLES-001: nome da role e unico.
        if await self.repository.get_by_name(data.name) is not None:
            raise ConflictError(
                "Ja existe uma role com este nome",
                details={"field": "name", "code": "ROLE_NAME_ALREADY_EXISTS"},
            )

        # `permissions=[]` explicito: sem isso, o atributo fica "nao carregado"
        # apos o INSERT e o Pydantic (sincrono) dispara um SELECT lazy
        # (selectin) fora de contexto async ao serializar -> MissingGreenlet.
        role = RoleModel(name=data.name, description=data.description, permissions=[])
        await self.repository.add(role)
        await self.repository.session.commit()
        return role

    async def get(self, role_id: uuid.UUID) -> RoleModel:
        role = await self.repository.get_by_id(role_id)
        if role is None:
            raise NotFoundError(
                "Role nao encontrada", details={"role_id": str(role_id), "code": "ROLE_NOT_FOUND"}
            )
        return role

    async def list(self, *, limit: int, offset: int) -> tuple[list[RoleModel], int]:
        roles = await self.repository.list(limit=limit, offset=offset)
        total = await self.repository.count()
        return roles, total

    async def update(self, role_id: uuid.UUID, data: RoleUpdate) -> RoleModel:
        role = await self.get(role_id)

        if data.name is not None and data.name != role.name:
            # RN-ROLES-001 tambem vale na atualizacao.
            if await self.repository.get_by_name(data.name) is not None:
                raise ConflictError(
                    "Ja existe uma role com este nome",
                    details={"field": "name", "code": "ROLE_NAME_ALREADY_EXISTS"},
                )
            role.name = data.name

        if data.description is not None:
            role.description = data.description

        await self.repository.session.commit()
        return await self.repository.refresh(role)

    async def delete(self, role_id: uuid.UUID) -> None:
        role = await self.get(role_id)

        # RN-ROLES-002: role em uso nao pode ser removida.
        if await self.user_repository.count_by_role_id(role_id) > 0:
            raise ConflictError(
                "Role esta em uso por um ou mais usuarios", details={"code": "ROLE_IN_USE"}
            )

        await self.repository.delete(role)
        await self.repository.session.commit()

    async def set_permissions(self, role_id: uuid.UUID, data: RolePermissionsUpdate) -> RoleModel:
        role = await self.get(role_id)

        permissions = await self.permission_repository.get_by_ids(data.permission_ids)
        found_ids = {permission.id for permission in permissions}
        missing_ids = [pid for pid in data.permission_ids if pid not in found_ids]
        if missing_ids:
            raise NotFoundError(
                "Uma ou mais permissions nao existem",
                details={
                    "permission_ids": [str(pid) for pid in missing_ids],
                    "code": "PERMISSION_NOT_FOUND",
                },
            )

        await self.repository.set_permissions(role, permissions)
        await self.repository.session.commit()
        return await self.repository.refresh(role)

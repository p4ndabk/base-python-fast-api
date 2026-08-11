"""Acesso a dados de roles.

Camada REPOSITORY: unico lugar do modulo que monta query e usa a sessao.

Convencao de transacao: o repository usa `flush()`; quem chama `commit()` e
o SERVICE.
"""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.permissions.models import PermissionModel
from app.modules.roles.models import RoleModel


class RoleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, role_id: uuid.UUID) -> RoleModel | None:
        result = await self.session.execute(select(RoleModel).where(RoleModel.id == role_id))
        return result.scalars().first()

    async def get_by_name(self, name: str) -> RoleModel | None:
        result = await self.session.execute(select(RoleModel).where(RoleModel.name == name))
        return result.scalars().first()

    async def count(self) -> int:
        result = await self.session.execute(select(func.count()).select_from(RoleModel))
        return int(result.scalar_one())

    async def add(self, role: RoleModel) -> RoleModel:
        self.session.add(role)
        await self.session.flush()
        return role

    async def delete(self, role: RoleModel) -> None:
        await self.session.delete(role)
        await self.session.flush()

    async def refresh(self, role: RoleModel) -> RoleModel:
        await self.session.refresh(role)
        return role

    async def set_permissions(
        self, role: RoleModel, permissions: list[PermissionModel]
    ) -> RoleModel:
        role.permissions = permissions
        await self.session.flush()
        return role

    async def count_users_with_role(self, role_id: uuid.UUID) -> int:
        # RN-ROLES-002: usado para bloquear remocao de role em uso.
        from app.modules.users.models import UserModel

        result = await self.session.execute(
            select(func.count()).select_from(UserModel).where(UserModel.role_id == role_id)
        )
        return int(result.scalar_one())

    async def list(self, *, limit: int, offset: int) -> list[RoleModel]:
        # Definido por ultimo na classe de proposito: um metodo chamado `list`
        # vira nome local do corpo da classe e sombreia o builtin `list` nas
        # anotacoes (`list[...]`) de qualquer metodo declarado DEPOIS dele.
        result = await self.session.execute(
            select(RoleModel).order_by(RoleModel.created_at.desc()).limit(limit).offset(offset)
        )
        return list(result.scalars().all())

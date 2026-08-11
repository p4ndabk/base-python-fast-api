"""Acesso a dados de permissions.

Camada REPOSITORY: unico lugar do modulo que monta query e usa a sessao.
"""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.permissions.models import PermissionModel


class PermissionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def count(self) -> int:
        result = await self.session.execute(select(func.count()).select_from(PermissionModel))
        return int(result.scalar_one())

    async def get_by_ids(self, permission_ids: list[uuid.UUID]) -> list[PermissionModel]:
        result = await self.session.execute(
            select(PermissionModel).where(PermissionModel.id.in_(permission_ids))
        )
        return list(result.scalars().all())

    async def list(self, *, limit: int, offset: int) -> list[PermissionModel]:
        # Definido por ultimo na classe de proposito: um metodo chamado `list`
        # vira nome local do corpo da classe e sombreia o builtin `list` nas
        # anotacoes (`list[...]`) de qualquer metodo declarado DEPOIS dele.
        result = await self.session.execute(
            select(PermissionModel).order_by(PermissionModel.code).limit(limit).offset(offset)
        )
        return list(result.scalars().all())

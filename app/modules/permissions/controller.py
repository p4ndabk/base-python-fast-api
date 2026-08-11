"""Orquestracao do modulo permissions."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.schemas import Page
from app.modules.permissions.repository import PermissionRepository
from app.modules.permissions.schemas import PermissionRead
from app.modules.permissions.service import PermissionService


class PermissionController:
    def __init__(self, session: AsyncSession) -> None:
        self.service = PermissionService(PermissionRepository(session))

    async def list(self, *, limit: int, offset: int) -> Page[PermissionRead]:
        permissions, total = await self.service.list(limit=limit, offset=offset)
        return Page[PermissionRead](
            items=[PermissionRead.model_validate(p) for p in permissions],
            total=total,
            limit=limit,
            offset=offset,
        )

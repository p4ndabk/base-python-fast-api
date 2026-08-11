"""Orquestracao do modulo users.

Camada CONTROLLER: monta o service, chama o metodo certo e converte model ->
schema de saida. Nao contem regra de negocio nem query.
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.schemas import Page
from app.modules.roles.repository import RoleRepository
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import UserCreate, UserRead, UserUpdate
from app.modules.users.service import UserService


class UserController:
    def __init__(self, session: AsyncSession) -> None:
        self.service = UserService(UserRepository(session), RoleRepository(session))

    async def create(self, data: UserCreate) -> UserRead:
        user = await self.service.create(data)
        return UserRead.model_validate(user)

    async def get(self, user_id: uuid.UUID) -> UserRead:
        user = await self.service.get(user_id)
        return UserRead.model_validate(user)

    async def list(self, *, limit: int, offset: int) -> Page[UserRead]:
        users, total = await self.service.list(limit=limit, offset=offset)
        return Page[UserRead](
            items=[UserRead.model_validate(user) for user in users],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def update(self, user_id: uuid.UUID, data: UserUpdate) -> UserRead:
        user = await self.service.update(user_id, data)
        return UserRead.model_validate(user)

    async def delete(self, user_id: uuid.UUID) -> None:
        await self.service.delete(user_id)

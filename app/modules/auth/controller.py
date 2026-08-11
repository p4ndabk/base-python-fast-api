"""Orquestracao do modulo auth."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.schemas import TokenPair
from app.modules.auth.service import AuthService
from app.modules.roles.repository import RoleRepository
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import UserCreate, UserRead


class AuthController:
    def __init__(self, session: AsyncSession) -> None:
        self.service = AuthService(UserRepository(session), RoleRepository(session))

    async def register(self, data: UserCreate) -> UserRead:
        user = await self.service.register(data)
        return UserRead.model_validate(user)

    async def login(self, email: str, password: str) -> TokenPair:
        return await self.service.login(email, password)

    async def refresh(self, refresh_token: str) -> TokenPair:
        return await self.service.refresh(refresh_token)

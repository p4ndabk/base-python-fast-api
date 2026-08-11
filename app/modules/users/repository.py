"""Acesso a dados de usuarios.

Camada REPOSITORY: unico lugar do modulo que monta query e usa a sessao.
Nao decide nada de negocio - so le e escreve.

Convencao de transacao: o repository usa `flush()` (garante o INSERT e popula o
id); quem chama `commit()` e o SERVICE, que conhece o limite da operacao.
"""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.users.models import UserModel


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, user_id: uuid.UUID) -> UserModel | None:
        result = await self.session.execute(select(UserModel).where(UserModel.id == user_id))
        return result.scalars().first()

    async def get_by_email(self, email: str) -> UserModel | None:
        result = await self.session.execute(select(UserModel).where(UserModel.email == email))
        return result.scalars().first()

    async def list(self, *, limit: int, offset: int) -> list[UserModel]:
        result = await self.session.execute(
            select(UserModel).order_by(UserModel.created_at.desc()).limit(limit).offset(offset)
        )
        return list(result.scalars().all())

    async def count(self) -> int:
        result = await self.session.execute(select(func.count()).select_from(UserModel))
        return int(result.scalar_one())

    async def add(self, user: UserModel) -> UserModel:
        self.session.add(user)
        await self.session.flush()
        return user

    async def delete(self, user: UserModel) -> None:
        await self.session.delete(user)
        await self.session.flush()

    async def refresh(self, user: UserModel) -> UserModel:
        """Recarrega o objeto do banco.

        Necessario depois de um UPDATE: colunas com `onupdate` server-side (como
        `updated_at`) ficam expiradas apos o commit, e le-las fora de um contexto
        async quebra com MissingGreenlet.
        """
        await self.session.refresh(user)
        return user

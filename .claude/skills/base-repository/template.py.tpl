"""Acesso a dados de {{entities}}.

Camada REPOSITORY: unico lugar do modulo que monta query e usa a sessao.
Nao decide nada de negocio - so le e escreve.

Convencao de transacao: aqui usa-se `flush()`; quem chama `commit()` e o SERVICE.
"""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.{{entities}}.models import {{Entity}}Model


class {{Entity}}Repository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, {{entity}}_id: uuid.UUID) -> {{Entity}}Model | None:
        result = await self.session.execute(
            select({{Entity}}Model).where({{Entity}}Model.id == {{entity}}_id)
        )
        return result.scalars().first()

    async def list(self, *, limit: int, offset: int) -> list[{{Entity}}Model]:
        result = await self.session.execute(
            select({{Entity}}Model)
            .order_by({{Entity}}Model.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def count(self) -> int:
        result = await self.session.execute(select(func.count()).select_from({{Entity}}Model))
        return int(result.scalar_one())

    async def add(self, {{entity}}: {{Entity}}Model) -> {{Entity}}Model:
        self.session.add({{entity}})
        await self.session.flush()
        return {{entity}}

    async def delete(self, {{entity}}: {{Entity}}Model) -> None:
        await self.session.delete({{entity}})
        await self.session.flush()

    async def refresh(self, {{entity}}: {{Entity}}Model) -> {{Entity}}Model:
        await self.session.refresh({{entity}})
        return {{entity}}

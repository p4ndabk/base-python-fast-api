"""Orquestracao do modulo {{entities}}.

Camada CONTROLLER: monta o service, chama o metodo certo e converte
model -> schema de saida. Sem regra de negocio, sem query.
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.schemas import Page
from app.modules.{{entities}}.repository import {{Entity}}Repository
from app.modules.{{entities}}.schemas import {{Entity}}Create, {{Entity}}Read, {{Entity}}Update
from app.modules.{{entities}}.service import {{Entity}}Service


class {{Entity}}Controller:
    def __init__(self, session: AsyncSession) -> None:
        self.service = {{Entity}}Service({{Entity}}Repository(session))

    async def create(self, data: {{Entity}}Create) -> {{Entity}}Read:
        {{entity}} = await self.service.create(data)
        return {{Entity}}Read.model_validate({{entity}})

    async def get(self, {{entity}}_id: uuid.UUID) -> {{Entity}}Read:
        {{entity}} = await self.service.get({{entity}}_id)
        return {{Entity}}Read.model_validate({{entity}})

    async def list(self, *, limit: int, offset: int) -> Page[{{Entity}}Read]:
        items, total = await self.service.list(limit=limit, offset=offset)
        return Page[{{Entity}}Read](
            items=[{{Entity}}Read.model_validate(item) for item in items],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def update(self, {{entity}}_id: uuid.UUID, data: {{Entity}}Update) -> {{Entity}}Read:
        {{entity}} = await self.service.update({{entity}}_id, data)
        return {{Entity}}Read.model_validate({{entity}})

    async def delete(self, {{entity}}_id: uuid.UUID) -> None:
        await self.service.delete({{entity}}_id)

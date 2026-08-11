"""Regras de negocio de {{entities}}.

Camada SERVICE: onde as regras de `.rules/{{entities}}/RULES.md` sao implementadas.
Cada validacao cita o ID da regra (ex: # RN-{{ENTITIES}}-001) para dar rastreabilidade.

Proibido aqui: HTTPException, Request, select(). Use erros de dominio.
"""

import uuid

from app.core.exceptions import NotFoundError
from app.modules.{{entities}}.models import {{Entity}}Model
from app.modules.{{entities}}.repository import {{Entity}}Repository
from app.modules.{{entities}}.schemas import {{Entity}}Create, {{Entity}}Update


class {{Entity}}Service:
    def __init__(self, repository: {{Entity}}Repository) -> None:
        self.repository = repository

    async def create(self, data: {{Entity}}Create) -> {{Entity}}Model:
        {{entity}} = {{Entity}}Model(**data.model_dump())
        await self.repository.add({{entity}})
        await self.repository.session.commit()
        return {{entity}}

    async def get(self, {{entity}}_id: uuid.UUID) -> {{Entity}}Model:
        {{entity}} = await self.repository.get_by_id({{entity}}_id)
        if {{entity}} is None:
            raise NotFoundError(
                "{{Entity}} nao encontrado", details={"{{entity}}_id": str({{entity}}_id)}
            )
        return {{entity}}

    async def list(self, *, limit: int, offset: int) -> tuple[list[{{Entity}}Model], int]:
        items = await self.repository.list(limit=limit, offset=offset)
        total = await self.repository.count()
        return items, total

    async def update(self, {{entity}}_id: uuid.UUID, data: {{Entity}}Update) -> {{Entity}}Model:
        {{entity}} = await self.get({{entity}}_id)

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr({{entity}}, field, value)

        await self.repository.session.commit()
        return await self.repository.refresh({{entity}})

    async def delete(self, {{entity}}_id: uuid.UUID) -> None:
        {{entity}} = await self.get({{entity}}_id)
        await self.repository.delete({{entity}})
        await self.repository.session.commit()

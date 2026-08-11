"""EXEMPLO da camada CONTROLLER — `app/modules/products/controller.py`.

Referência viva no repositório: `app/modules/users/controller.py`.
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.schemas import Page
from app.modules.products.repository import ProductRepository
from app.modules.products.schemas import ProductCreate, ProductRead, ProductUpdate
from app.modules.products.service import ProductService


class ProductController:
    def __init__(self, session: AsyncSession) -> None:
        # ok o grafo de dependencias e montado UMA vez, aqui
        self.service = ProductService(ProductRepository(session))

    async def create(self, data: ProductCreate) -> ProductRead:
        product = await self.service.create(data)
        # ok model -> schema. Sem isso, o SQLAlchemy vazaria para a resposta
        return ProductRead.model_validate(product)

    async def get(self, product_id: uuid.UUID) -> ProductRead:
        # ok se o service lancar NotFoundError, ele SOBE ate o handler global.
        #    Nao capture aqui so para relancar como HTTPException.
        product = await self.service.get(product_id)
        return ProductRead.model_validate(product)

    async def list(self, *, limit: int, offset: int) -> Page[ProductRead]:
        products, total = await self.service.list(limit=limit, offset=offset)
        # ok o envelope de paginacao e montado aqui, com o mesmo formato em toda a API
        return Page[ProductRead](
            items=[ProductRead.model_validate(p) for p in products],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def update(self, product_id: uuid.UUID, data: ProductUpdate) -> ProductRead:
        product = await self.service.update(product_id, data)
        return ProductRead.model_validate(product)

    async def delete(self, product_id: uuid.UUID) -> None:
        # ok 204 nao tem corpo: o metodo devolve None
        await self.service.delete(product_id)

    # no NUNCA aqui:
    # async def create(self, data):
    #     if await self.service.repository.get_by_sku(data.sku):   <- regra -> service
    #         raise HTTPException(status_code=409)                 <- erro HTTP -> handler global
    #     return await self.service.create(data)                   <- devolveria MODEL, nao schema

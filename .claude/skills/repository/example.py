"""EXEMPLO da camada REPOSITORY — `app/modules/products/repository.py`.

Referência viva no repositório: `app/modules/users/repository.py`.
"""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.products.models import ProductModel


class ProductRepository:
    # ok recebe a sessao pronta; nunca cria a propria sessao
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, product_id: uuid.UUID) -> ProductModel | None:
        # ok devolve None quando nao acha - quem transforma em 404 e o service
        result = await self.session.execute(
            select(ProductModel).where(ProductModel.id == product_id)
        )
        return result.scalars().first()

    async def get_by_sku(self, sku: str) -> ProductModel | None:
        # ok metodo de busca por campo unico: usado pelo service para checar duplicidade
        result = await self.session.execute(select(ProductModel).where(ProductModel.sku == sku))
        return result.scalars().first()

    async def list(
        self, *, limit: int, offset: int, only_active: bool = False
    ) -> list[ProductModel]:
        # ok paginacao no SQL (.limit/.offset), nunca fatiando lista em Python
        stmt = select(ProductModel).order_by(ProductModel.created_at.desc())

        if only_active:
            # ok filtro tecnico (traduz um parametro da rota) pode ficar aqui.
            #    Filtro que decide POLITICA de negocio fica no service.
            stmt = stmt.where(ProductModel.is_active.is_(True))

        result = await self.session.execute(stmt.limit(limit).offset(offset))
        return list(result.scalars().all())

    async def list_with_category(self, *, limit: int, offset: int) -> list[ProductModel]:
        # ok selectinload evita N+1 quando o relacionamento sera lido
        result = await self.session.execute(
            select(ProductModel)
            .options(selectinload(ProductModel.category))
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def count(self) -> int:
        # ok COUNT no banco; scalar_one() aqui e seguro porque count sempre devolve 1 linha
        result = await self.session.execute(select(func.count()).select_from(ProductModel))
        return int(result.scalar_one())

    async def add(self, product: ProductModel) -> ProductModel:
        self.session.add(product)
        # ok flush envia o INSERT e popula o id; o commit e do service
        await self.session.flush()
        return product

    async def delete(self, product: ProductModel) -> None:
        await self.session.delete(product)
        await self.session.flush()

    async def refresh(self, product: ProductModel) -> ProductModel:
        # ok necessario depois de UPDATE: `updated_at` tem onupdate server-side e
        #    fica expirado apos o commit (le-lo fora do contexto async quebra)
        await self.session.refresh(product)
        return product

    # no NUNCA aqui:
    # async def create(self, data: ProductCreate):
    #     if await self.get_by_sku(data.sku):        <- regra de negocio -> service
    #         raise ConflictError(...)               <- erro de dominio  -> service
    #     ...
    #     await self.session.commit()                <- commit           -> service

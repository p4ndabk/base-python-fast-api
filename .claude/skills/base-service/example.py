"""EXEMPLO da camada SERVICE — `app/modules/products/service.py`.

Referência viva no repositório: `app/modules/users/service.py`.
"""

import uuid

from app.core.exceptions import ConflictError, DomainValidationError, NotFoundError
from app.modules.products.models import ProductModel
from app.modules.products.repository import ProductRepository
from app.modules.products.schemas import ProductCreate, ProductUpdate


class ProductService:
    # ok recebe o repository pronto; nunca cria sessao
    def __init__(self, repository: ProductRepository) -> None:
        self.repository = repository

    async def create(self, data: ProductCreate) -> ProductModel:
        # ok cada regra cita o ID de .rules/ - permite `grep RN-PRODUCTS-001`
        # RN-PRODUCTS-001: SKU e unico no sistema.
        if await self.repository.get_by_sku(data.sku) is not None:
            # ok erro de DOMINIO; o handler global traduz para HTTP 409
            raise ConflictError(
                "Ja existe produto com este SKU",
                details={"field": "sku", "code": "SKU_ALREADY_EXISTS"},
            )

        product = ProductModel(**data.model_dump())
        await self.repository.add(product)

        # ok o commit e do service: ele conhece o limite da operacao
        await self.repository.session.commit()
        return product  # ok devolve MODEL - a conversao para schema e do controller

    async def get(self, product_id: uuid.UUID) -> ProductModel:
        product = await self.repository.get_by_id(product_id)
        if product is None:
            # ok o repository devolveu None; e AQUI que isso vira 404
            raise NotFoundError("Produto nao encontrado", details={"product_id": str(product_id)})
        return product

    async def list(self, *, limit: int, offset: int) -> tuple[list[ProductModel], int]:
        products = await self.repository.list(limit=limit, offset=offset)
        total = await self.repository.count()
        return products, total

    async def update(self, product_id: uuid.UUID, data: ProductUpdate) -> ProductModel:
        product = await self.get(product_id)  # ok reaproveita o 404

        if data.sku is not None and data.sku != product.sku:
            # RN-PRODUCTS-001 tambem vale na atualizacao.
            if await self.repository.get_by_sku(data.sku) is not None:
                raise ConflictError(
                    "Ja existe produto com este SKU",
                    details={"field": "sku", "code": "SKU_ALREADY_EXISTS"},
                )
            product.sku = data.sku

        if data.name is not None:
            product.name = data.name
        if data.price is not None:
            product.price = data.price
        if data.is_active is not None:
            product.is_active = data.is_active

        await self.repository.session.commit()
        # ok refresh obrigatorio apos UPDATE: recarrega o `updated_at` do banco
        return await self.repository.refresh(product)

    async def deactivate(self, product_id: uuid.UUID) -> ProductModel:
        """Exemplo de regra que NAO cabe no schema: depende do estado atual."""
        product = await self.get(product_id)

        # RN-PRODUCTS-003: produto ja inativo nao pode ser desativado de novo.
        if not product.is_active:
            raise DomainValidationError("Produto ja esta inativo")

        product.is_active = False
        await self.repository.session.commit()
        return await self.repository.refresh(product)

    async def delete(self, product_id: uuid.UUID) -> None:
        product = await self.get(product_id)
        await self.repository.delete(product)
        await self.repository.session.commit()

    # no NUNCA aqui:
    # from fastapi import HTTPException
    # raise HTTPException(status_code=404, detail="nao encontrado")   -> NotFoundError
    #
    # result = await self.repository.session.execute(select(...))     -> peca um metodo ao repository
    #
    # return ProductRead.model_validate(product)                      -> conversao e do controller

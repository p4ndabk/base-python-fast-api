"""EXEMPLO de TESTE DE SERVICE com repository fake — `tests/test_products_service.py`.

Prova a regra de negócio isolada, sem HTTP e sem banco. Rápido: ideal quando a
regra tem muitos ramos e testar tudo por rota ficaria lento.
"""

import uuid

import pytest

from app.core.exceptions import ConflictError, NotFoundError
from app.modules.products.models import ProductModel
from app.modules.products.schemas import ProductCreate
from app.modules.products.service import ProductService


class FakeSession:
    """Substitui a AsyncSession: so registra que o commit foi chamado."""

    def __init__(self) -> None:
        self.committed = False

    async def commit(self) -> None:
        self.committed = True


class FakeProductRepository:
    """Repository em memoria com a MESMA interface do real.

    ok implementa exatamente os metodos que o service usa - nem mais, nem menos.
    """

    def __init__(self, produtos: list[ProductModel] | None = None) -> None:
        self.produtos = produtos or []
        self.session = FakeSession()

    async def get_by_id(self, product_id: uuid.UUID) -> ProductModel | None:
        return next((p for p in self.produtos if p.id == product_id), None)

    async def get_by_sku(self, sku: str) -> ProductModel | None:
        return next((p for p in self.produtos if p.sku == sku), None)

    async def add(self, product: ProductModel) -> ProductModel:
        product.id = product.id or uuid.uuid4()
        self.produtos.append(product)
        return product

    async def refresh(self, product: ProductModel) -> ProductModel:
        return product


async def test_create_persiste_e_commita() -> None:
    repository = FakeProductRepository()
    service = ProductService(repository)

    product = await service.create(
        ProductCreate(name="Teclado", sku="TEC-001", price="199.90")
    )

    assert product.sku == "TEC-001"
    assert repository.session.committed is True  # ok prova que houve commit


async def test_create_com_sku_duplicado_levanta_conflict() -> None:
    """RN-PRODUCTS-001: SKU e unico no sistema."""
    existente = ProductModel(id=uuid.uuid4(), name="Ja existe", sku="TEC-001", price="10.00")
    service = ProductService(FakeProductRepository([existente]))

    # ok testa o ERRO DE DOMINIO, nao o status HTTP - o service nao conhece HTTP
    with pytest.raises(ConflictError):
        await service.create(ProductCreate(name="Novo", sku="TEC-001", price="199.90"))


async def test_get_inexistente_levanta_not_found() -> None:
    service = ProductService(FakeProductRepository())

    with pytest.raises(NotFoundError):
        await service.get(uuid.uuid4())

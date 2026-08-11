"""EXEMPLO da camada ROUTER — `app/modules/products/router.py`.

Referência viva no repositório: `app/modules/users/router.py`.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Query, status

from app.api.deps import CurrentUserDep, SessionDep
from app.core.schemas import ErrorResponse, Page
from app.modules.products.controller import ProductController
from app.modules.products.schemas import ProductCreate, ProductRead, ProductUpdate

# ok prefix no plural + tags (agrupa as rotas no /docs)
router = APIRouter(prefix="/products", tags=["products"])


@router.post(
    "",
    response_model=ProductRead,  # ok sempre declarado
    status_code=status.HTTP_201_CREATED,  # ok 201 em criacao
    summary="Cria um produto",
    responses={  # ok cada erro possivel documentado
        409: {"model": ErrorResponse, "description": "SKU ja cadastrado"},
        401: {"model": ErrorResponse, "description": "Nao autenticado"},
    },
)
async def create_product(
    data: ProductCreate,
    session: SessionDep,
    _: CurrentUserDep,  # ok rota protegida: basta declarar a dependencia
) -> ProductRead:
    # ok uma linha, delegando ao controller
    return await ProductController(session).create(data)


# ⚠️ ORDEM IMPORTA: rotas literais ANTES das parametricas.
# Se `/products/{product_id}` viesse antes, "featured" seria lido como um id.
@router.get(
    "/featured",
    response_model=list[ProductRead],
    status_code=status.HTTP_200_OK,
    summary="Lista os produtos em destaque",
)
async def list_featured(session: SessionDep) -> list[ProductRead]:
    return await ProductController(session).list_featured()


@router.get(
    "",
    response_model=Page[ProductRead],  # ok envelope padrao de paginacao
    status_code=status.HTTP_200_OK,
    summary="Lista produtos (paginado)",
)
async def list_products(
    session: SessionDep,
    # ok limite maximo de 100 (RN-GLOBAL-003) declarado na propria assinatura
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Page[ProductRead]:
    return await ProductController(session).list(limit=limit, offset=offset)


@router.get(
    "/{product_id}",
    response_model=ProductRead,
    status_code=status.HTTP_200_OK,
    summary="Busca um produto por id",
    responses={404: {"model": ErrorResponse, "description": "Produto nao encontrado"}},
)
async def get_product(product_id: uuid.UUID, session: SessionDep) -> ProductRead:
    # ok o tipo uuid.UUID ja valida o path param (422 automatico se vier lixo)
    return await ProductController(session).get(product_id)


@router.patch(
    "/{product_id}",
    response_model=ProductRead,
    status_code=status.HTTP_200_OK,
    summary="Atualiza um produto (parcial)",
    responses={
        404: {"model": ErrorResponse, "description": "Produto nao encontrado"},
        409: {"model": ErrorResponse, "description": "SKU ja cadastrado"},
    },
)
async def update_product(
    product_id: uuid.UUID,
    data: ProductUpdate,
    session: SessionDep,
    _: CurrentUserDep,
) -> ProductRead:
    return await ProductController(session).update(product_id, data)


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,  # ok 204 nao declara response_model
    summary="Remove um produto",
    responses={404: {"model": ErrorResponse, "description": "Produto nao encontrado"}},
)
async def delete_product(product_id: uuid.UUID, session: SessionDep, _: CurrentUserDep) -> None:
    await ProductController(session).delete(product_id)


# no NUNCA aqui:
# @router.post("/create-product")                  <- acao no path; use POST /products
# def create(...)                                  <- rota sincrona; use async def
# @router.get("/{id}")                             <- sem response_model
# async def get(...):
#     if not produto.is_active:                    <- regra de negocio -> service
#         raise HTTPException(400)                 <- erro HTTP -> erro de dominio
#     result = await session.execute(select(...))  <- query -> repository
#
# E NAO ESQUECA: registrar em app/api/v1.py
#   from app.modules.products.router import router as products_router
#   api_router.include_router(products_router)

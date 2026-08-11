"""Rotas de {{entities}}.

Camada ROUTER: caminho, metodo, status code, response_model e dependencias.
Zero logica. Toda funcao e `async def` e delega ao controller.

DEPOIS DE CRIAR ESTE ARQUIVO, registre em `app/api/v1.py`:
    from app.modules.{{entities}}.router import router as {{entities}}_router
    api_router.include_router({{entities}}_router)
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Query, status

from app.api.deps import CurrentUserDep, SessionDep
from app.core.schemas import ErrorResponse, Page
from app.modules.{{entities}}.controller import {{Entity}}Controller
from app.modules.{{entities}}.schemas import {{Entity}}Create, {{Entity}}Read, {{Entity}}Update

router = APIRouter(prefix="/{{entities}}", tags=["{{entities}}"])


@router.post(
    "",
    response_model={{Entity}}Read,
    status_code=status.HTTP_201_CREATED,
    summary="Cria um {{entity}}",
    responses={401: {"model": ErrorResponse, "description": "Nao autenticado"}},
)
async def create_{{entity}}(
    data: {{Entity}}Create, session: SessionDep, _: CurrentUserDep
) -> {{Entity}}Read:
    return await {{Entity}}Controller(session).create(data)


@router.get(
    "",
    response_model=Page[{{Entity}}Read],
    status_code=status.HTTP_200_OK,
    summary="Lista {{entities}} (paginado)",
)
async def list_{{entities}}(
    session: SessionDep,
    _: CurrentUserDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Page[{{Entity}}Read]:
    return await {{Entity}}Controller(session).list(limit=limit, offset=offset)


@router.get(
    "/{{{entity}}_id}",
    response_model={{Entity}}Read,
    status_code=status.HTTP_200_OK,
    summary="Busca um {{entity}} por id",
    responses={404: {"model": ErrorResponse, "description": "{{Entity}} nao encontrado"}},
)
async def get_{{entity}}(
    {{entity}}_id: uuid.UUID, session: SessionDep, _: CurrentUserDep
) -> {{Entity}}Read:
    return await {{Entity}}Controller(session).get({{entity}}_id)


@router.patch(
    "/{{{entity}}_id}",
    response_model={{Entity}}Read,
    status_code=status.HTTP_200_OK,
    summary="Atualiza um {{entity}} (parcial)",
    responses={404: {"model": ErrorResponse, "description": "{{Entity}} nao encontrado"}},
)
async def update_{{entity}}(
    {{entity}}_id: uuid.UUID, data: {{Entity}}Update, session: SessionDep, _: CurrentUserDep
) -> {{Entity}}Read:
    return await {{Entity}}Controller(session).update({{entity}}_id, data)


@router.delete(
    "/{{{entity}}_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove um {{entity}}",
    responses={404: {"model": ErrorResponse, "description": "{{Entity}} nao encontrado"}},
)
async def delete_{{entity}}(
    {{entity}}_id: uuid.UUID, session: SessionDep, _: CurrentUserDep
) -> None:
    await {{Entity}}Controller(session).delete({{entity}}_id)

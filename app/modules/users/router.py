"""Rotas de usuarios.

Camada ROUTER: caminho, metodo, status code, response_model e dependencias.
Zero logica. Toda funcao e `async def` e delega ao controller.

RN-USERS-004: so `POST /users` e publica; as demais exigem `CurrentUserDep`.
RN-GLOBAL-003: listagem paginada com limit 1..100 e offset >= 0.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Query, status

from app.api.deps import CurrentUserDep, SessionDep
from app.core.schemas import ErrorResponse, Page
from app.modules.users.controller import UserController
from app.modules.users.schemas import UserCreate, UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.post(
    "",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Cria um usuario",
    responses={409: {"model": ErrorResponse, "description": "E-mail ja cadastrado"}},
)
async def create_user(data: UserCreate, session: SessionDep) -> UserRead:
    return await UserController(session).create(data)


@router.get(
    "",
    response_model=Page[UserRead],
    status_code=status.HTTP_200_OK,
    summary="Lista usuarios (paginado)",
)
async def list_users(
    session: SessionDep,
    _: CurrentUserDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Page[UserRead]:
    return await UserController(session).list(limit=limit, offset=offset)


@router.get(
    "/{user_id}",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Busca um usuario por id",
    responses={404: {"model": ErrorResponse, "description": "Usuario nao encontrado"}},
)
async def get_user(user_id: uuid.UUID, session: SessionDep, _: CurrentUserDep) -> UserRead:
    return await UserController(session).get(user_id)


@router.patch(
    "/{user_id}",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Atualiza um usuario (parcial)",
    responses={
        404: {"model": ErrorResponse, "description": "Usuario nao encontrado"},
        409: {"model": ErrorResponse, "description": "E-mail ja cadastrado"},
    },
)
async def update_user(
    user_id: uuid.UUID,
    data: UserUpdate,
    session: SessionDep,
    _: CurrentUserDep,
) -> UserRead:
    return await UserController(session).update(user_id, data)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove um usuario",
    responses={404: {"model": ErrorResponse, "description": "Usuario nao encontrado"}},
)
async def delete_user(user_id: uuid.UUID, session: SessionDep, _: CurrentUserDep) -> None:
    await UserController(session).delete(user_id)

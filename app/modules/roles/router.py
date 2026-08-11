"""Rotas de roles.

RN-ROLES-003: toda rota deste modulo exige a permission `roles:manage`,
alem de autenticacao.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import RequirePermission, SessionDep
from app.core.permissions import PermissionCode
from app.core.schemas import ErrorResponse, Page
from app.modules.roles.controller import RoleController
from app.modules.roles.schemas import RoleCreate, RolePermissionsUpdate, RoleRead, RoleUpdate

router = APIRouter(prefix="/roles", tags=["roles"])

_RequireRolesManage = Depends(RequirePermission(PermissionCode.ROLES_MANAGE))


@router.post(
    "",
    response_model=RoleRead,
    status_code=status.HTTP_201_CREATED,
    summary="Cria uma role",
    responses={409: {"model": ErrorResponse, "description": "Nome de role ja cadastrado"}},
)
async def create_role(
    data: RoleCreate, session: SessionDep, _: Annotated[None, _RequireRolesManage]
) -> RoleRead:
    return await RoleController(session).create(data)


@router.get(
    "",
    response_model=Page[RoleRead],
    status_code=status.HTTP_200_OK,
    summary="Lista roles (paginado)",
)
async def list_roles(
    session: SessionDep,
    _: Annotated[None, _RequireRolesManage],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Page[RoleRead]:
    return await RoleController(session).list(limit=limit, offset=offset)


@router.get(
    "/{role_id}",
    response_model=RoleRead,
    status_code=status.HTTP_200_OK,
    summary="Busca uma role por id",
    responses={404: {"model": ErrorResponse, "description": "Role nao encontrada"}},
)
async def get_role(
    role_id: uuid.UUID, session: SessionDep, _: Annotated[None, _RequireRolesManage]
) -> RoleRead:
    return await RoleController(session).get(role_id)


@router.patch(
    "/{role_id}",
    response_model=RoleRead,
    status_code=status.HTTP_200_OK,
    summary="Atualiza uma role (parcial)",
    responses={
        404: {"model": ErrorResponse, "description": "Role nao encontrada"},
        409: {"model": ErrorResponse, "description": "Nome de role ja cadastrado"},
    },
)
async def update_role(
    role_id: uuid.UUID,
    data: RoleUpdate,
    session: SessionDep,
    _: Annotated[None, _RequireRolesManage],
) -> RoleRead:
    return await RoleController(session).update(role_id, data)


@router.delete(
    "/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove uma role",
    responses={
        404: {"model": ErrorResponse, "description": "Role nao encontrada"},
        409: {"model": ErrorResponse, "description": "Role em uso por usuarios"},
    },
)
async def delete_role(
    role_id: uuid.UUID, session: SessionDep, _: Annotated[None, _RequireRolesManage]
) -> None:
    await RoleController(session).delete(role_id)


@router.put(
    "/{role_id}/permissions",
    response_model=RoleRead,
    status_code=status.HTTP_200_OK,
    summary="Substitui as permissions de uma role",
    responses={
        404: {"model": ErrorResponse, "description": "Role ou permission nao encontrada"},
    },
)
async def set_role_permissions(
    role_id: uuid.UUID,
    data: RolePermissionsUpdate,
    session: SessionDep,
    _: Annotated[None, _RequireRolesManage],
) -> RoleRead:
    return await RoleController(session).set_permissions(role_id, data)

"""Rotas de permissions.

RN-PERMISSIONS-002: GET /permissions exige autenticacao, sem permission
especifica (catalogo e somente leitura para qualquer usuario logado).
"""

from typing import Annotated

from fastapi import APIRouter, Query, status

from app.api.deps import CurrentUserDep, SessionDep
from app.core.schemas import Page
from app.modules.permissions.controller import PermissionController
from app.modules.permissions.schemas import PermissionRead

router = APIRouter(prefix="/permissions", tags=["permissions"])


@router.get(
    "",
    response_model=Page[PermissionRead],
    status_code=status.HTTP_200_OK,
    summary="Lista o catalogo de permissions (paginado)",
)
async def list_permissions(
    session: SessionDep,
    _: CurrentUserDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Page[PermissionRead]:
    return await PermissionController(session).list(limit=limit, offset=offset)

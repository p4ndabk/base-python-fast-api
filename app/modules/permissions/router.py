"""Rotas de permissions.

RN-PERMISSIONS-002: GET /permissions exige autenticacao e a permission
`permissions:read`.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import RequirePermission, SessionDep
from app.core.permissions import PermissionCode
from app.core.schemas import Page
from app.modules.permissions.controller import PermissionController
from app.modules.permissions.schemas import PermissionRead

router = APIRouter(prefix="/permissions", tags=["permissions"])

_require_permissions_read = Depends(RequirePermission(PermissionCode.PERMISSIONS_READ))


@router.get(
    "",
    response_model=Page[PermissionRead],
    status_code=status.HTTP_200_OK,
    summary="Lista o catalogo de permissions (paginado)",
)
async def list_permissions(
    session: SessionDep,
    _: Annotated[None, _require_permissions_read],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Page[PermissionRead]:
    return await PermissionController(session).list(limit=limit, offset=offset)

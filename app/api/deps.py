"""Dependencias compartilhadas entre modulos.

Aqui ficam apenas dependencias TRANSVERSAIS (usadas por mais de um modulo).
Dependencia especifica de um modulo mora no proprio modulo.
"""

from collections.abc import Awaitable, Callable
from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.permissions import PermissionCode
from app.core.security import decode_token
from app.database.session import get_session
from app.modules.users.models import UserModel
from app.modules.users.repository import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def get_current_user(
    session: SessionDep,
    token: Annotated[str | None, Depends(oauth2_scheme)],
) -> UserModel:
    """Resolve o usuario autenticado a partir do Bearer token.

    RN-AUTH-004: usuario inativo nao acessa rotas protegidas, mesmo com token valido.
    """
    if not token:
        raise UnauthorizedError("Credenciais nao fornecidas")

    user_id = decode_token(token, expected_type="access")

    user = await UserRepository(session).get_by_id(_to_uuid(user_id))
    if user is None:
        raise UnauthorizedError("Usuario do token nao existe mais")
    if not user.is_active:
        raise UnauthorizedError("Usuario inativo")

    return user


CurrentUserDep = Annotated[UserModel, Depends(get_current_user)]


def RequirePermission(code: PermissionCode) -> Callable[[UserModel], Awaitable[None]]:
    """Fabrica de dependencia: bloqueia quem nao tem a permission `code`.

    Uso: `_: Annotated[None, Depends(RequirePermission(PermissionCode.X))]`.

    RN-ROLES-004: usuario sem role nao tem nenhuma permission (fail closed).
    RN-ROLES-005: usuario cuja role nao tem `code` e bloqueado.

    Consulta SEMPRE `current_user.role` (carregado do banco nesta request) -
    RN-AUTH-006: as claims do access token NUNCA sao usadas para autorizar,
    so para introspeccao pelo cliente.
    """

    async def _check(current_user: CurrentUserDep) -> None:
        codes = (
            {permission.code for permission in current_user.role.permissions}
            if current_user.role
            else set()
        )
        if code.value not in codes:
            raise ForbiddenError(
                "Usuario nao tem permissao para esta acao",
                details={"permission": code.value},
            )

    return _check


def _to_uuid(value: str):
    import uuid

    try:
        return uuid.UUID(value)
    except ValueError as exc:
        raise UnauthorizedError("Token com identificacao invalida") from exc

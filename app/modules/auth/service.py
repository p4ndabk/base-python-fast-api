"""Regras de negocio de autenticacao.

Este service depende do REPOSITORY de outro modulo (`users`) - esse e o unico
tipo de dependencia permitida entre modulos. Nunca importe o router ou o
controller de outro modulo.
"""

import uuid

from app.core.config import settings
from app.core.exceptions import UnauthorizedError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.modules.auth.schemas import TokenPair
from app.modules.roles.repository import RoleRepository
from app.modules.users.models import UserModel
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import UserCreate
from app.modules.users.service import UserService


class AuthService:
    def __init__(self, user_repository: UserRepository, role_repository: RoleRepository) -> None:
        self.user_repository = user_repository
        self.user_service = UserService(user_repository, role_repository)

    async def register(self, data: UserCreate) -> UserModel:
        """Registro publico: reaproveita integralmente a regra de criacao de usuario."""
        return await self.user_service.create(data)

    async def login(self, email: str, password: str) -> TokenPair:
        user = await self.user_repository.get_by_email(email)

        # RN-AUTH-002: a resposta e identica para e-mail inexistente e senha errada,
        # para nao revelar quais e-mails estao cadastrados.
        if user is None or not verify_password(password, user.hashed_password):
            raise UnauthorizedError("E-mail ou senha invalidos")

        # RN-AUTH-004: usuario inativo nao autentica.
        if not user.is_active:
            raise UnauthorizedError("Usuario inativo")

        return self._issue_tokens(user)

    async def refresh(self, refresh_token: str) -> TokenPair:
        # RN-AUTH-003: so um token do tipo "refresh" e aceito aqui.
        subject = decode_token(refresh_token, expected_type="refresh")

        try:
            user_id = uuid.UUID(subject)
        except ValueError as exc:
            raise UnauthorizedError("Token com identificacao invalida") from exc

        user = await self.user_repository.get_by_id(user_id)
        if user is None or not user.is_active:
            raise UnauthorizedError("Usuario invalido para renovacao de token")

        return self._issue_tokens(user)

    def _issue_tokens(self, user: UserModel) -> TokenPair:
        # RN-AUTH-006: role/permissions vao no access token so como claims de
        # introspeccao - `user.role` ja vem carregado (lazy="selectin" no
        # model), sempre refletindo o estado atual no momento da emissao.
        role_name = user.role.name if user.role else None
        permission_codes = [p.code for p in user.role.permissions] if user.role else []

        return TokenPair(
            access_token=create_access_token(
                str(user.id), role=role_name, permissions=permission_codes
            ),
            refresh_token=create_refresh_token(str(user.id)),
            expires_in=settings.access_token_expire_minutes * 60,
        )

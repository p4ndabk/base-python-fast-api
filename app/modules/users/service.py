"""Regras de negocio de usuarios.

Camada SERVICE: onde as regras de `.rules/users/RULES.md` sao implementadas.
Cada validacao cita o ID da regra para dar rastreabilidade (grep RN-USERS-002).

Proibido aqui: HTTPException, Request, `select()`. Use erros de dominio.
"""

import uuid

from app.core.exceptions import ConflictError, NotFoundError
from app.core.security import hash_password
from app.modules.roles.repository import RoleRepository
from app.modules.users.models import UserModel
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import UserCreate, UserUpdate


class UserService:
    def __init__(self, repository: UserRepository, role_repository: RoleRepository) -> None:
        self.repository = repository
        self.role_repository = role_repository

    async def create(self, data: UserCreate) -> UserModel:
        # RN-USERS-002: e-mail e unico no sistema.
        if await self.repository.get_by_email(data.email) is not None:
            raise ConflictError(
                "Ja existe um usuario com este e-mail",
                details={"field": "email", "code": "EMAIL_ALREADY_EXISTS"},
            )

        # RN-AUTH-001: a senha nunca e persistida em texto puro.
        # RN-USERS-003: usuario nasce ativo; o cliente nao escolhe esse valor.
        user = UserModel(
            email=data.email,
            full_name=data.full_name,
            hashed_password=hash_password(data.password),
            is_active=True,
        )
        await self.repository.add(user)
        await self.repository.session.commit()
        return user

    async def get(self, user_id: uuid.UUID) -> UserModel:
        user = await self.repository.get_by_id(user_id)
        if user is None:
            raise NotFoundError("Usuario nao encontrado", details={"user_id": str(user_id)})
        return user

    async def list(self, *, limit: int, offset: int) -> tuple[list[UserModel], int]:
        users = await self.repository.list(limit=limit, offset=offset)
        total = await self.repository.count()
        return users, total

    async def update(self, user_id: uuid.UUID, data: UserUpdate) -> UserModel:
        user = await self.get(user_id)

        if data.email is not None and data.email != user.email:
            # RN-USERS-002 tambem vale na atualizacao.
            if await self.repository.get_by_email(data.email) is not None:
                raise ConflictError(
                    "Ja existe um usuario com este e-mail",
                    details={"field": "email", "code": "EMAIL_ALREADY_EXISTS"},
                )
            user.email = data.email

        if data.full_name is not None:
            user.full_name = data.full_name
        if data.password is not None:
            user.hashed_password = hash_password(data.password)
        if data.is_active is not None:
            user.is_active = data.is_active

        # RN-USERS-005: role_id ausente do payload nao mexe na role; presente
        # (mesmo `null`) atualiza. `null` remove a role do usuario.
        if "role_id" in data.model_fields_set:
            if (
                data.role_id is not None
                and await self.role_repository.get_by_id(data.role_id) is None
            ):
                raise NotFoundError(
                    "Role nao encontrada",
                    details={"role_id": str(data.role_id), "code": "ROLE_NOT_FOUND"},
                )
            user.role_id = data.role_id

        await self.repository.session.commit()
        # Recarrega para trazer o `updated_at` novo gerado pelo banco.
        return await self.repository.refresh(user)

    async def delete(self, user_id: uuid.UUID) -> None:
        user = await self.get(user_id)
        await self.repository.delete(user)
        await self.repository.session.commit()

"""Tabela de usuarios.

Camada MODEL: so mapeamento de tabela. Nenhuma regra de negocio, nenhum Pydantic.
"""

import uuid

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import GUID, Base, TimestampMixin
from app.modules.roles.models import RoleModel


class UserModel(Base, TimestampMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # RN-USERS-005: nullable - usuario sem role nao tem nenhuma permission.
    # ondelete=RESTRICT reforca RN-ROLES-002 (role em uso nao pode ser removida).
    role_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("roles.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    # lazy="selectin": RequirePermission (app/api/deps.py) le current_user.role
    # sem precisar de selectinload manual em cada query que carrega o usuario.
    role: Mapped[RoleModel | None] = relationship(lazy="selectin")

    def __repr__(self) -> str:
        return f"<UserModel id={self.id} email={self.email}>"

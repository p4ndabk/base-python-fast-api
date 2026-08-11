"""Tabela de roles e a associacao N:N com permissions.

Camada MODEL: so mapeamento de tabela. Nenhuma regra de negocio, nenhum Pydantic.
"""

from sqlalchemy import Column, ForeignKey, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import GUID, Base, TimestampMixin
from app.modules.permissions.models import PermissionModel

role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", GUID(), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column(
        "permission_id", GUID(), ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True
    ),
)


class RoleModel(Base, TimestampMixin):
    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # RN-ROLES-004/005: carregada sempre (lazy="selectin") para que
    # RequirePermission consulte codes de permission sem query manual extra.
    permissions: Mapped[list[PermissionModel]] = relationship(
        secondary=role_permissions, lazy="selectin", order_by=PermissionModel.code
    )

    def __repr__(self) -> str:
        return f"<RoleModel id={self.id} name={self.name}>"

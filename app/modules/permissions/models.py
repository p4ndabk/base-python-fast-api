"""Tabela do catalogo de permissions.

Camada MODEL: so mapeamento de tabela. Nenhuma regra de negocio, nenhum Pydantic.

RN-PERMISSIONS-001: o catalogo e fixo (populado por migration a partir de
`app.core.permissions.PermissionCode`) - nao existe rota de escrita aqui.
"""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class PermissionModel(Base, TimestampMixin):
    __tablename__ = "permissions"

    code: Mapped[str] = mapped_column(String(150), unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    def __repr__(self) -> str:
        return f"<PermissionModel id={self.id} code={self.code}>"

"""Tabela de {{entities}}.

Camada MODEL: so mapeamento de tabela. Nenhuma regra de negocio, nenhum Pydantic.

DEPOIS DE CRIAR ESTE ARQUIVO:
  1. importe este modulo em `alembic/env.py`
  2. rode `uv run alembic revision --autogenerate -m "cria tabela {{entities}}"`
"""

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class {{Entity}}Model(Base, TimestampMixin):
    __tablename__ = "{{entities}}"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<{{Entity}}Model id={self.id}>"

"""Base declarativa do SQLAlchemy e mixins compartilhados.

TODO model do projeto herda de `Base` + `TimestampMixin`. Isso garante que todas
as tabelas tenham id UUID e timestamps em UTC, sem repeticao.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import CHAR, TypeDecorator


class GUID(TypeDecorator):
    """UUID que funciona em Postgres (nativo) e SQLite (CHAR(36), usado nos testes)."""

    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PGUUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))


class Base(DeclarativeBase):
    """Base declarativa. O Alembic descobre as tabelas por `Base.metadata`."""

    type_annotation_map = {uuid.UUID: GUID}


class TimestampMixin:
    """id + created_at + updated_at. Herde em todo model.

    RN-GLOBAL-001: os timestamps sao gerados pelo BANCO (`server_default=now()`)
    com timezone, nunca pelo codigo da aplicacao.
    """

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

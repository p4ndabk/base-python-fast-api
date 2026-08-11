"""EXEMPLO da camada MODEL — `app/modules/products/models.py`.

Referência viva no repositório: `app/modules/users/models.py`.
"""

from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class ProductModel(Base, TimestampMixin):
    # ok plural, snake_case
    __tablename__ = "products"

    # ok id, created_at e updated_at ja vem do TimestampMixin - nao redeclare

    # ok tamanho explicito + index em coluna usada no WHERE
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # ok unicidade tambem no banco: o service valida antes (mensagem boa),
    #    o banco garante sob concorrencia (ultima linha de defesa)
    sku: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)

    # ok dinheiro e Numeric, nunca Float (Float perde centavos)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    # ok campo opcional: Mapped[X | None] + nullable=True, coerente com o schema
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # ok FK: o tipo tem que casar com o id da outra tabela (UUID via TimestampMixin)
    category_id: Mapped[str | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )
    category: Mapped["CategoryModel | None"] = relationship(back_populates="products")

    # no NUNCA aqui: validacao de negocio
    #    def validar_preco(self): if self.price <= 0: raise ...   -> vai para service.py
    # no NUNCA aqui: query
    #    @classmethod def buscar_por_sku(cls, session, sku)       -> vai para repository.py
    # no NUNCA aqui: Pydantic
    #    class Config: orm_mode = True                            -> vai para schemas.py

    def __repr__(self) -> str:
        return f"<ProductModel id={self.id} sku={self.sku}>"


class CategoryModel(Base, TimestampMixin):
    __tablename__ = "categories"

    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    products: Mapped[list[ProductModel]] = relationship(back_populates="category")

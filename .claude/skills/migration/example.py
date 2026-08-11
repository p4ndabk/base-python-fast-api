"""EXEMPLO de MIGRATION — `alembic/versions/0002_cria_tabela_products.py`.

Referência viva no repositório: `alembic/versions/0001_cria_tabela_users.py`.

Este arquivo mostra o que revisar numa migration gerada por --autogenerate.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# ok confira o encadeamento: down_revision aponta para a revisao ANTERIOR
revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "products",
        # ok o id vem do TimestampMixin: UUID, nao Integer
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("sku", sa.String(length=64), nullable=False),
        # ok dinheiro: Numeric com precisao explicita, nunca Float
        sa.Column("price", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        # ok timestamps com timezone e default do BANCO (RN-GLOBAL-001)
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    # ok o unique=True do model vira um indice unico aqui - confira se veio
    op.create_index(op.f("ix_products_sku"), "products", ["sku"], unique=True)
    op.create_index(op.f("ix_products_name"), "products", ["name"], unique=False)


def downgrade() -> None:
    # ok ordem INVERSA do upgrade: primeiro os indices, depois a tabela
    op.drop_index(op.f("ix_products_name"), table_name="products")
    op.drop_index(op.f("ix_products_sku"), table_name="products")
    op.drop_table("products")
    # no NUNCA deixe `pass` aqui - sem downgrade nao ha rollback


# --- Padrao para ADICIONAR COLUNA NOT NULL em tabela que JA TEM DADOS ---------
#
# no ERRADO (quebra na hora de aplicar):
#     op.add_column("products", sa.Column("category", sa.String(50), nullable=False))
#
# ok CERTO - opcao A: com server_default
#     op.add_column("products", sa.Column(
#         "category", sa.String(50), nullable=False, server_default="geral"))
#
# ok CERTO - opcao B: tres passos, quando nao existe default razoavel
#     op.add_column("products", sa.Column("category", sa.String(50), nullable=True))
#     op.execute("UPDATE products SET category = 'geral' WHERE category IS NULL")
#     op.alter_column("products", "category", nullable=False)
#
# --- RENOMEAR COLUNA ---------------------------------------------------------
#
# no O autogenerate gera DROP + CREATE e VOCE PERDE OS DADOS.
# ok Corrija a mao para:
#     op.alter_column("products", "nome_antigo", new_column_name="nome_novo")

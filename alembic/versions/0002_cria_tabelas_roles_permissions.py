"""cria tabelas roles, permissions, role_permissions; users ganha role_id

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-11

Seed: popula `permissions` a partir de `app.core.permissions.PermissionCode`
e cria a role "admin" com todas as permissions do seed. O catalogo de
permissions e fixo (RN-PERMISSIONS-001) - se `PermissionCode` ganhar um
membro novo depois desta migration, ele entra numa migration de seed nova,
nao editando esta (migration aplicada nao se edita).
"""

import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Espelha app.core.permissions.PermissionCode no momento em que esta
# migration foi escrita - ver docstring acima.
_SEED_PERMISSIONS = [
    ("roles:manage", "Gerenciar roles e as permissions de cada role"),
    ("permissions:read", "Listar o catalogo de permissions"),
]
_SEED_ADMIN_ROLE_NAME = "admin"


def upgrade() -> None:
    op.create_table(
        "permissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(length=150), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
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
    op.create_index(op.f("ix_permissions_code"), "permissions", ["code"], unique=True)

    op.create_table(
        "roles",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
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
    op.create_index(op.f("ix_roles_name"), "roles", ["name"], unique=True)

    op.create_table(
        "role_permissions",
        sa.Column("role_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("permission_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["permission_id"], ["permissions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("role_id", "permission_id"),
    )

    op.add_column("users", sa.Column("role_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index(op.f("ix_users_role_id"), "users", ["role_id"])
    op.create_foreign_key(
        "fk_users_role_id_roles", "users", "roles", ["role_id"], ["id"], ondelete="RESTRICT"
    )

    _seed_admin_role_and_permissions()


def _seed_admin_role_and_permissions() -> None:
    permissions_table = sa.table(
        "permissions",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("code", sa.String),
        sa.column("description", sa.String),
    )
    roles_table = sa.table(
        "roles",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("name", sa.String),
        sa.column("description", sa.String),
    )
    role_permissions_table = sa.table(
        "role_permissions",
        sa.column("role_id", postgresql.UUID(as_uuid=True)),
        sa.column("permission_id", postgresql.UUID(as_uuid=True)),
    )

    permission_ids = [uuid.uuid4() for _ in _SEED_PERMISSIONS]
    op.bulk_insert(
        permissions_table,
        [
            {"id": permission_id, "code": code, "description": description}
            for permission_id, (code, description) in zip(
                permission_ids, _SEED_PERMISSIONS, strict=True
            )
        ],
    )

    admin_role_id = uuid.uuid4()
    op.bulk_insert(
        roles_table,
        [
            {
                "id": admin_role_id,
                "name": _SEED_ADMIN_ROLE_NAME,
                "description": "Acesso total a administracao do sistema",
            }
        ],
    )

    op.bulk_insert(
        role_permissions_table,
        [
            {"role_id": admin_role_id, "permission_id": permission_id}
            for permission_id in permission_ids
        ],
    )


def downgrade() -> None:
    op.drop_constraint("fk_users_role_id_roles", "users", type_="foreignkey")
    op.drop_index(op.f("ix_users_role_id"), table_name="users")
    op.drop_column("users", "role_id")

    op.drop_table("role_permissions")

    op.drop_index(op.f("ix_roles_name"), table_name="roles")
    op.drop_table("roles")

    op.drop_index(op.f("ix_permissions_code"), table_name="permissions")
    op.drop_table("permissions")

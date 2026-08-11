"""seed da permission users:manage, adicionada a role admin

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-11

Seed: adiciona `users:manage` (novo membro de `app.core.permissions.PermissionCode`)
ao catalogo de `permissions` e a role "admin" existente. Nao edita a migration
0002 (migration aplicada nao se edita) - ver docstring de 0002.
"""

import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_PERMISSION_CODE = "users:manage"
_PERMISSION_DESCRIPTION = "Alterar dados administrativos de usuarios (ex.: role_id)"
_ADMIN_ROLE_NAME = "admin"


def upgrade() -> None:
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
    )
    role_permissions_table = sa.table(
        "role_permissions",
        sa.column("role_id", postgresql.UUID(as_uuid=True)),
        sa.column("permission_id", postgresql.UUID(as_uuid=True)),
    )

    conn = op.get_bind()

    permission_id = uuid.uuid4()
    op.bulk_insert(
        permissions_table,
        [{"id": permission_id, "code": _PERMISSION_CODE, "description": _PERMISSION_DESCRIPTION}],
    )

    admin_role_id = conn.execute(
        sa.select(roles_table.c.id).where(roles_table.c.name == _ADMIN_ROLE_NAME)
    ).scalar_one_or_none()
    if admin_role_id is not None:
        op.bulk_insert(
            role_permissions_table,
            [{"role_id": admin_role_id, "permission_id": permission_id}],
        )


def downgrade() -> None:
    conn = op.get_bind()

    permissions_table = sa.table(
        "permissions", sa.column("id", postgresql.UUID(as_uuid=True)), sa.column("code", sa.String)
    )
    permission_id = conn.execute(
        sa.select(permissions_table.c.id).where(permissions_table.c.code == _PERMISSION_CODE)
    ).scalar_one_or_none()

    if permission_id is not None:
        role_permissions_table = sa.table(
            "role_permissions", sa.column("permission_id", postgresql.UUID(as_uuid=True))
        )
        op.execute(
            role_permissions_table.delete().where(
                role_permissions_table.c.permission_id == permission_id
            )
        )
        op.execute(permissions_table.delete().where(permissions_table.c.id == permission_id))

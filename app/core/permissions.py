"""Catalogo de codigos de permission.

Unica fonte de verdade dos codigos: o seed da migration e todo
`RequirePermission(...)` usado em routers referenciam este enum. NUNCA
escreva um codigo de permission como string solta em outro arquivo.
"""

from enum import StrEnum


class PermissionCode(StrEnum):
    # roles
    ROLES_MANAGE = "roles:manage"

    # permissions
    PERMISSIONS_READ = "permissions:read"

    # users
    USERS_MANAGE = "users:manage"

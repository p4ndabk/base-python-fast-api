"""Rastreabilidade entre `PermissionCode` e o seed das migrations.

`PermissionCode` (app/core/permissions.py) e a fonte de verdade declarada;
o seed real fica espalhado pelas migrations de `alembic/versions/` porque
uma migration ja aplicada nao pode ser editada para acompanhar o enum.

Este teste carrega cada migration por caminho (sem aplicar upgrade/downgrade,
so o corpo do modulo) e confere que a uniao dos codes semeados e exatamente
igual ao enum. Convencao exigida de toda migration de seed nova: expor
`_SEED_PERMISSIONS` (lista de tuplas `(code, description)`) ou
`_PERMISSION_CODE` (string) como constante de modulo.
"""

import importlib.util
from pathlib import Path

from app.core.permissions import PermissionCode

_VERSIONS_DIR = Path(__file__).resolve().parent.parent / "alembic" / "versions"


def _load_migration_module(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _seeded_codes() -> set[str]:
    codes: set[str] = set()
    for path in sorted(_VERSIONS_DIR.glob("*.py")):
        module = _load_migration_module(path)
        seed_permissions = getattr(module, "_SEED_PERMISSIONS", None)
        if seed_permissions is not None:
            codes.update(code for code, _description in seed_permissions)
        permission_code = getattr(module, "_PERMISSION_CODE", None)
        if permission_code is not None:
            codes.add(permission_code)
    return codes


def test_seed_das_migrations_cobre_todo_permissioncode() -> None:
    """Todo membro de PermissionCode precisa ter sido semeado por alguma migration."""
    enum_codes = {code.value for code in PermissionCode}

    assert _seeded_codes() == enum_codes, (
        "PermissionCode e o seed das migrations divergiram. Ao adicionar um "
        "membro novo em PermissionCode, crie uma migration de seed nova "
        "(nao edite uma ja aplicada) expondo _SEED_PERMISSIONS ou "
        "_PERMISSION_CODE."
    )

"""Testes do modulo roles (rota + regras de negocio + RequirePermission)."""

import uuid

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.permissions.models import PermissionModel
from app.modules.roles.models import RoleModel
from app.modules.users.repository import UserRepository


async def test_cria_role(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    response = await client.post(
        "/roles",
        json={"name": "operator", "description": "Opera o catalogo"},
        headers=admin_headers,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "operator"
    assert body["permissions"] == []


async def test_nome_duplicado_retorna_409(
    client: AsyncClient, admin_headers: dict[str, str]
) -> None:
    """RN-ROLES-001: nome da role e unico."""
    await client.post("/roles", json={"name": "operator"}, headers=admin_headers)

    response = await client.post("/roles", json={"name": "operator"}, headers=admin_headers)

    assert response.status_code == 409
    assert response.json()["error"]["details"]["code"] == "ROLE_NAME_ALREADY_EXISTS"


async def test_criar_role_sem_permission_retorna_403(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    """RN-ROLES-003: gerenciar roles exige a permission roles:manage."""
    response = await client.post("/roles", json={"name": "operator"}, headers=auth_headers)

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


async def test_criar_role_sem_autenticacao_retorna_401(client: AsyncClient) -> None:
    response = await client.post("/roles", json={"name": "operator"})

    assert response.status_code == 401


async def test_substitui_permissions_da_role(
    client: AsyncClient, admin_headers: dict[str, str], db_session: AsyncSession
) -> None:
    created = await client.post("/roles", json={"name": "operator"}, headers=admin_headers)
    role_id = created.json()["id"]

    permission = PermissionModel(code="products:create", description="Criar produto")
    db_session.add(permission)
    await db_session.commit()

    response = await client.put(
        f"/roles/{role_id}/permissions",
        json={"permission_ids": [str(permission.id)]},
        headers=admin_headers,
    )

    assert response.status_code == 200
    codes = {item["code"] for item in response.json()["permissions"]}
    assert codes == {"products:create"}


async def test_atribuir_permission_inexistente_retorna_404(
    client: AsyncClient, admin_headers: dict[str, str]
) -> None:
    created = await client.post("/roles", json={"name": "operator"}, headers=admin_headers)
    role_id = created.json()["id"]

    response = await client.put(
        f"/roles/{role_id}/permissions",
        json={"permission_ids": [str(uuid.uuid4())]},
        headers=admin_headers,
    )

    assert response.status_code == 404
    assert response.json()["error"]["details"]["code"] == "PERMISSION_NOT_FOUND"


async def test_remove_role_em_uso_retorna_409(
    client: AsyncClient,
    admin_headers: dict[str, str],
    db_session: AsyncSession,
    user_payload: dict[str, str],
) -> None:
    """RN-ROLES-002: role com usuario vinculado nao pode ser removida."""
    created = await client.post("/roles", json={"name": "operator"}, headers=admin_headers)
    role_id = created.json()["id"]

    other_user = await client.post(
        "/users",
        json={"email": "outro@exemplo.com", "full_name": "Outro", "password": "senha12345"},
    )
    await client.patch(
        f"/users/{other_user.json()['id']}", json={"role_id": role_id}, headers=admin_headers
    )

    response = await client.delete(f"/roles/{role_id}", headers=admin_headers)

    assert response.status_code == 409
    assert response.json()["error"]["details"]["code"] == "ROLE_IN_USE"


async def test_remove_role_sem_uso_funciona(
    client: AsyncClient, admin_headers: dict[str, str]
) -> None:
    created = await client.post("/roles", json={"name": "temp"}, headers=admin_headers)
    role_id = created.json()["id"]

    response = await client.delete(f"/roles/{role_id}", headers=admin_headers)

    assert response.status_code == 204

    followup = await client.get(f"/roles/{role_id}", headers=admin_headers)
    assert followup.status_code == 404


async def test_require_permission_bloqueia_usuario_sem_role(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    """RN-ROLES-004: usuario sem role_id nao tem nenhuma permission."""
    response = await client.post("/roles", json={"name": "qualquer"}, headers=auth_headers)

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


async def test_require_permission_bloqueia_usuario_sem_a_permission(
    client: AsyncClient, db_session: AsyncSession, user_payload: dict[str, str]
) -> None:
    """RN-ROLES-005: usuario autenticado, mas cuja role nao tem a permission exigida."""
    await client.post("/auth/register", json=user_payload)

    permission = PermissionModel(code="permissions:read", description="Listar permissions")
    role = RoleModel(name="reader", description="So le", permissions=[permission])
    db_session.add_all([permission, role])
    await db_session.flush()

    user = await UserRepository(db_session).get_by_email(user_payload["email"])
    user.role_id = role.id
    await db_session.commit()

    login = await client.post(
        "/auth/login",
        json={"email": user_payload["email"], "password": user_payload["password"]},
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    response = await client.post("/roles", json={"name": "qualquer"}, headers=headers)

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


async def test_require_permission_libera_usuario_com_a_permission(
    client: AsyncClient, admin_headers: dict[str, str]
) -> None:
    """RN-ROLES-005 (caminho feliz): role com a permission exigida passa."""
    response = await client.post("/roles", json={"name": "operator"}, headers=admin_headers)

    assert response.status_code == 201

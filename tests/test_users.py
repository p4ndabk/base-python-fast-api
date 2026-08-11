"""Testes do modulo users (rota + regras de negocio)."""

import uuid

from httpx import AsyncClient


async def test_cria_usuario(client: AsyncClient, user_payload: dict[str, str]) -> None:
    response = await client.post("/users", json=user_payload)

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == user_payload["email"]
    assert body["is_active"] is True
    assert "hashed_password" not in body  # senha nunca vaza na resposta
    assert "password" not in body


async def test_email_duplicado_retorna_409(
    client: AsyncClient, user_payload: dict[str, str]
) -> None:
    """RN-USERS-002: e-mail e unico no sistema."""
    await client.post("/users", json=user_payload)

    response = await client.post("/users", json=user_payload)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "CONFLICT"


async def test_email_normalizado_para_lowercase(client: AsyncClient) -> None:
    """RN-GLOBAL-002: e-mail e normalizado antes de persistir."""
    response = await client.post(
        "/users",
        json={"email": "  Joao@Exemplo.COM ", "full_name": "Joao", "password": "senha12345"},
    )

    assert response.status_code == 201
    assert response.json()["email"] == "joao@exemplo.com"


async def test_senha_curta_retorna_422(client: AsyncClient) -> None:
    """RN-USERS-001: senha tem no minimo 8 caracteres."""
    response = await client.post(
        "/users",
        json={"email": "ana@exemplo.com", "full_name": "Ana", "password": "1234"},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "UNPROCESSABLE_ENTITY"


async def test_busca_usuario_por_id(
    client: AsyncClient, auth_headers: dict[str, str], user_payload: dict[str, str]
) -> None:
    created = await client.post(
        "/users",
        json={"email": "outro@exemplo.com", "full_name": "Outro", "password": "senha12345"},
    )
    user_id = created.json()["id"]

    response = await client.get(f"/users/{user_id}", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["id"] == user_id


async def test_usuario_inexistente_retorna_404(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    response = await client.get(f"/users/{uuid.uuid4()}", headers=auth_headers)

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


async def test_lista_usuarios_paginada(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    for i in range(3):
        await client.post(
            "/users",
            json={
                "email": f"user{i}@exemplo.com",
                "full_name": f"User {i}",
                "password": "senha12345",
            },
        )

    response = await client.get("/users?limit=2&offset=0", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 2
    assert body["total"] == 4  # 3 criados + o usuario do auth_headers
    assert body["limit"] == 2
    assert body["offset"] == 0


async def test_lista_sem_token_retorna_401(client: AsyncClient) -> None:
    response = await client.get("/users")

    assert response.status_code == 401


async def test_atualiza_usuario(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    created = await client.post(
        "/users",
        json={"email": "pedro@exemplo.com", "full_name": "Pedro", "password": "senha12345"},
    )
    user_id = created.json()["id"]

    response = await client.patch(
        f"/users/{user_id}", json={"full_name": "Pedro Souza"}, headers=auth_headers
    )

    assert response.status_code == 200
    assert response.json()["full_name"] == "Pedro Souza"


async def test_atribui_role_a_usuario(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    """RN-USERS-005: role_id valido e aceito e refletido no usuario."""
    role = await client.post("/roles", json={"name": "operator"}, headers=admin_headers)
    role_id = role.json()["id"]

    created = await client.post(
        "/users",
        json={"email": "operador@exemplo.com", "full_name": "Operador", "password": "senha12345"},
    )
    user_id = created.json()["id"]

    response = await client.patch(
        f"/users/{user_id}", json={"role_id": role_id}, headers=admin_headers
    )

    assert response.status_code == 200
    assert response.json()["role_id"] == role_id


async def test_user_read_traz_role_aninhada(
    client: AsyncClient, admin_headers: dict[str, str]
) -> None:
    """RN-USERS-006: UserRead traz role com nome e permissions, nao so o id."""
    role = await client.post("/roles", json={"name": "operator"}, headers=admin_headers)
    role_id = role.json()["id"]

    created = await client.post(
        "/users",
        json={"email": "aninhado@exemplo.com", "full_name": "Aninhado", "password": "senha12345"},
    )
    user_id = created.json()["id"]

    response = await client.patch(
        f"/users/{user_id}", json={"role_id": role_id}, headers=admin_headers
    )

    assert response.status_code == 200
    body = response.json()
    assert body["role_id"] == role_id
    assert body["role"]["name"] == "operator"
    assert body["role"]["permissions"] == []


async def test_user_sem_role_traz_role_null(
    client: AsyncClient, user_payload: dict[str, str]
) -> None:
    """RN-USERS-006: usuario sem role_id traz role = null."""
    response = await client.post("/users", json=user_payload)

    assert response.json()["role_id"] is None
    assert response.json()["role"] is None


async def test_atribuir_role_inexistente_retorna_404(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    """RN-USERS-005: role_id que nao existe e rejeitado."""
    created = await client.post(
        "/users",
        json={
            "email": "operador2@exemplo.com",
            "full_name": "Operador 2",
            "password": "senha12345",
        },
    )
    user_id = created.json()["id"]

    response = await client.patch(
        f"/users/{user_id}", json={"role_id": str(uuid.uuid4())}, headers=auth_headers
    )

    assert response.status_code == 404
    assert response.json()["error"]["details"]["code"] == "ROLE_NOT_FOUND"


async def test_remove_usuario(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    created = await client.post(
        "/users",
        json={"email": "temp@exemplo.com", "full_name": "Temp", "password": "senha12345"},
    )
    user_id = created.json()["id"]

    response = await client.delete(f"/users/{user_id}", headers=auth_headers)
    assert response.status_code == 204

    followup = await client.get(f"/users/{user_id}", headers=auth_headers)
    assert followup.status_code == 404

"""Testes do modulo auth."""

from httpx import AsyncClient


async def test_registra_e_faz_login(client: AsyncClient, user_payload: dict[str, str]) -> None:
    register = await client.post("/auth/register", json=user_payload)
    assert register.status_code == 201

    response = await client.post(
        "/auth/login",
        json={"email": user_payload["email"], "password": user_payload["password"]},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["token_type"] == "bearer"
    assert body["expires_in"] > 0


async def test_login_com_senha_errada_retorna_401(
    client: AsyncClient, user_payload: dict[str, str]
) -> None:
    """RN-AUTH-002: mensagem generica, sem revelar se o e-mail existe."""
    await client.post("/auth/register", json=user_payload)

    response = await client.post(
        "/auth/login", json={"email": user_payload["email"], "password": "senha-errada"}
    )

    assert response.status_code == 401
    assert response.json()["error"]["message"] == "E-mail ou senha invalidos"


async def test_login_com_email_inexistente_retorna_mesma_mensagem(client: AsyncClient) -> None:
    """RN-AUTH-002: resposta identica ao caso de senha errada."""
    response = await client.post(
        "/auth/login", json={"email": "ninguem@exemplo.com", "password": "senha12345"}
    )

    assert response.status_code == 401
    assert response.json()["error"]["message"] == "E-mail ou senha invalidos"


async def test_me_com_token_valido(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    response = await client.get("/auth/me", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["email"] == "maria@exemplo.com"


async def test_me_sem_token_retorna_401(client: AsyncClient) -> None:
    response = await client.get("/auth/me")

    assert response.status_code == 401


async def test_me_com_token_invalido_retorna_401(client: AsyncClient) -> None:
    response = await client.get("/auth/me", headers={"Authorization": "Bearer token-falso"})

    assert response.status_code == 401


async def test_refresh_gera_novos_tokens(client: AsyncClient, user_payload: dict[str, str]) -> None:
    await client.post("/auth/register", json=user_payload)
    login = await client.post(
        "/auth/login",
        json={"email": user_payload["email"], "password": user_payload["password"]},
    )
    refresh_token = login.json()["refresh_token"]

    response = await client.post("/auth/refresh", json={"refresh_token": refresh_token})

    assert response.status_code == 200
    assert response.json()["access_token"]


async def test_access_token_nao_serve_como_refresh(
    client: AsyncClient, user_payload: dict[str, str]
) -> None:
    """RN-AUTH-003: o tipo do token e verificado explicitamente."""
    await client.post("/auth/register", json=user_payload)
    login = await client.post(
        "/auth/login",
        json={"email": user_payload["email"], "password": user_payload["password"]},
    )
    access_token = login.json()["access_token"]

    response = await client.post("/auth/refresh", json={"refresh_token": access_token})

    assert response.status_code == 401


async def test_usuario_inativo_nao_autentica(
    client: AsyncClient, user_payload: dict[str, str], auth_headers: dict[str, str]
) -> None:
    """RN-AUTH-004: usuario inativo nao faz login."""
    created = await client.post(
        "/users",
        json={"email": "inativo@exemplo.com", "full_name": "Inativo", "password": "senha12345"},
    )
    user_id = created.json()["id"]
    await client.patch(f"/users/{user_id}", json={"is_active": False}, headers=auth_headers)

    response = await client.post(
        "/auth/login", json={"email": "inativo@exemplo.com", "password": "senha12345"}
    )

    assert response.status_code == 401
    assert response.json()["error"]["message"] == "Usuario inativo"

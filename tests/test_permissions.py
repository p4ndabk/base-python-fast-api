"""Testes do modulo permissions."""

from httpx import AsyncClient


async def test_lista_catalogo_de_permissions(
    client: AsyncClient, admin_headers: dict[str, str], auth_headers: dict[str, str]
) -> None:
    """RN-PERMISSIONS-001: catalogo vem do seed (aqui, da fixture admin_headers)."""
    response = await client.get("/permissions", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 2
    codes = {item["code"] for item in body["items"]}
    assert "roles:manage" in codes
    assert "permissions:read" in codes


async def test_lista_sem_token_retorna_401(client: AsyncClient) -> None:
    """RN-PERMISSIONS-002: listar exige autenticacao."""
    response = await client.get("/permissions")

    assert response.status_code == 401

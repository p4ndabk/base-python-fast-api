"""Testes do modulo {{entities}}."""

import uuid

from httpx import AsyncClient

PAYLOAD = {"name": "Nome do {{entity}}"}


async def test_cria_{{entity}}(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    response = await client.post("/{{entities}}", json=PAYLOAD, headers=auth_headers)

    assert response.status_code == 201
    assert response.json()["name"] == PAYLOAD["name"]


async def test_{{entity}}_inexistente_retorna_404(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    response = await client.get(f"/{{entities}}/{uuid.uuid4()}", headers=auth_headers)

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


async def test_sem_token_retorna_401(client: AsyncClient) -> None:
    response = await client.get("/{{entities}}")

    assert response.status_code == 401


async def test_lista_paginada(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    for i in range(3):
        await client.post(
            "/{{entities}}", json={"name": f"Item {i}"}, headers=auth_headers
        )

    response = await client.get("/{{entities}}?limit=2&offset=0", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 2
    assert body["total"] == 3


async def test_remove_{{entity}}(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    created = await client.post("/{{entities}}", json=PAYLOAD, headers=auth_headers)
    {{entity}}_id = created.json()["id"]

    response = await client.delete(f"/{{entities}}/{{{entity}}_id}", headers=auth_headers)
    assert response.status_code == 204

    followup = await client.get(f"/{{entities}}/{{{entity}}_id}", headers=auth_headers)
    assert followup.status_code == 404

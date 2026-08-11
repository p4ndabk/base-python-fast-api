"""EXEMPLO de TESTE DE ROTA — `tests/test_products.py`.

Prova o contrato HTTP completo: status, corpo, autenticação.
Referência viva no repositório: `tests/test_users.py`.
"""

import uuid

from httpx import AsyncClient

# ok nada de @pytest.mark.asyncio: asyncio_mode="auto" no pyproject cuida disso

PAYLOAD = {"name": "Teclado mecanico", "sku": "TEC-001", "price": "199.90"}


async def test_cria_produto(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    response = await client.post("/products", json=PAYLOAD, headers=auth_headers)

    # ok status E corpo - so o status nao prova que a resposta esta certa
    assert response.status_code == 201
    body = response.json()
    assert body["sku"] == "TEC-001"
    assert body["id"]


async def test_sku_duplicado_retorna_409(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    """RN-PRODUCTS-001: SKU e unico no sistema."""  # ok ID da regra no docstring
    await client.post("/products", json=PAYLOAD, headers=auth_headers)

    response = await client.post("/products", json=PAYLOAD, headers=auth_headers)

    assert response.status_code == 409
    # ok asserta o `code`, que e estavel; a `message` pode ser reescrita
    assert response.json()["error"]["code"] == "CONFLICT"


async def test_preco_zero_retorna_422(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    """RN-PRODUCTS-002: preco e sempre maior que zero."""
    # ok validacao de schema e SEMPRE 422 (nao 400)
    response = await client.post(
        "/products", json={**PAYLOAD, "price": "0"}, headers=auth_headers
    )

    assert response.status_code == 422


async def test_produto_inexistente_retorna_404(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    response = await client.get(f"/products/{uuid.uuid4()}", headers=auth_headers)

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


async def test_criar_sem_token_retorna_401(client: AsyncClient) -> None:
    response = await client.post("/products", json=PAYLOAD)

    assert response.status_code == 401


async def test_lista_paginada(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    for i in range(3):
        await client.post(
            "/products", json={**PAYLOAD, "sku": f"SKU-{i}"}, headers=auth_headers
        )

    response = await client.get("/products?limit=2&offset=0", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 2
    assert body["total"] == 3
    assert body["limit"] == 2


async def test_remove_produto(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    created = await client.post("/products", json=PAYLOAD, headers=auth_headers)
    product_id = created.json()["id"]

    response = await client.delete(f"/products/{product_id}", headers=auth_headers)
    assert response.status_code == 204

    # ok prova que sumiu de verdade
    followup = await client.get(f"/products/{product_id}", headers=auth_headers)
    assert followup.status_code == 404

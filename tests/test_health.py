"""Testes do modulo health."""

from httpx import AsyncClient


async def test_liveness_retorna_ok(client: AsyncClient) -> None:
    response = await client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_readiness_com_banco_no_ar(client: AsyncClient) -> None:
    response = await client.get("/health/ready")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "up"
    assert body["latency_ms"] >= 0


async def test_readiness_com_banco_fora_retorna_503(client: AsyncClient, monkeypatch) -> None:
    """Se o SELECT 1 falha, a rota devolve 503 e diz que o banco esta down."""

    async def ping_quebrado(self) -> None:
        raise OSError("conexao recusada")

    monkeypatch.setattr(
        "app.modules.health.repository.HealthRepository.ping", ping_quebrado, raising=True
    )

    response = await client.get("/health/ready")

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "degraded"
    assert body["database"] == "down"

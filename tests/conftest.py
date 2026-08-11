"""Fixtures compartilhadas pela suite.

Estrategia: os testes rodam contra SQLite em memoria (aiosqlite), sem precisar de
Postgres no ambiente de CI ou na maquina do dev. O schema e criado a partir de
`Base.metadata`, exatamente como o Alembic faria.

Para rodar contra Postgres de verdade, defina TEST_DATABASE_URL no ambiente.
"""

import os
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.database.session import get_session
from app.main import app

# Importa todos os models para que Base.metadata conheca as tabelas
from app.modules.users import models  # noqa: F401

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite+aiosqlite:///:memory:")


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Banco limpo a cada teste: cria o schema, entrega a sessao, descarta tudo."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=StaticPool,  # mantem o :memory: vivo entre conexoes
        connect_args={"check_same_thread": False} if "sqlite" in TEST_DATABASE_URL else {},
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Cliente HTTP com a sessao de teste injetada no lugar da real."""

    async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_session] = override_get_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client

    app.dependency_overrides.clear()


@pytest.fixture
def user_payload() -> dict[str, str]:
    return {
        "email": "maria@exemplo.com",
        "full_name": "Maria Silva",
        "password": "senha-super-secreta",
    }


@pytest.fixture
async def auth_headers(client: AsyncClient, user_payload: dict[str, str]) -> dict[str, str]:
    """Registra um usuario e devolve o header Authorization pronto."""
    await client.post("/auth/register", json=user_payload)
    response = await client.post(
        "/auth/login",
        json={"email": user_payload["email"], "password": user_payload["password"]},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

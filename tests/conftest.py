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

from app.core.permissions import PermissionCode
from app.database.base import Base
from app.database.session import get_session
from app.main import app

# Importa todos os models para que Base.metadata conheca as tabelas
from app.modules.permissions.models import PermissionModel
from app.modules.roles.models import RoleModel
from app.modules.users import models  # noqa: F401
from app.modules.users.repository import UserRepository

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


@pytest.fixture
async def admin_headers(
    client: AsyncClient, db_session: AsyncSession, user_payload: dict[str, str]
) -> dict[str, str]:
    """Registra um usuario e o vincula a uma role com todas as permissions do seed.

    Equivalente, em teste, ao seed de producao (migration 0002) + atribuicao
    manual da role "admin" a um usuario (PT-01 do TODO.md da spec 0001):
    aqui a atribuicao e direta no banco porque nao existe rota publica para
    o primeiro bootstrap.
    """
    await client.post("/auth/register", json=user_payload)

    permissions = [
        PermissionModel(code=code.value, description=code.value) for code in PermissionCode
    ]
    role = RoleModel(name="admin", description="Acesso total", permissions=permissions)
    db_session.add_all([*permissions, role])
    await db_session.flush()

    # `user.role = role`, nao `user.role_id = role.id`: ver comentario em
    # tests/test_auth.py sobre por que o FK bruto pode deixar `.role` (ja
    # carregado por esta mesma query, lazy="selectin") desatualizado.
    user = await UserRepository(db_session).get_by_email(user_payload["email"])
    user.role = role
    await db_session.commit()

    response = await client.post(
        "/auth/login",
        json={"email": user_payload["email"], "password": user_payload["password"]},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

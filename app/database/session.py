"""Engine e sessao assincrona do SQLAlchemy.

`get_session` e a UNICA porta de entrada para o banco. Ela e injetada no router
via `Depends(get_session)` e repassada para baixo ate o repository.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

engine = create_async_engine(
    settings.database_url,
    echo=settings.database_echo,
    pool_pre_ping=True,  # derruba conexoes mortas antes de usar
    future=True,
)

SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # permite ler o objeto depois do commit (usado no controller)
    autoflush=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependencia do FastAPI: abre a sessao, garante rollback em erro e fecha."""
    async with SessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

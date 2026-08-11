"""Acesso ao banco para o health check.

Este modulo nao tem tabela propria: o repository existe apenas para manter a
regra "somente o repository fala com a sessao do banco".
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class HealthRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def ping(self) -> None:
        """Executa `SELECT 1`. Levanta a excecao original do driver se o banco estiver fora."""
        await self.session.execute(text("SELECT 1"))

"""Orquestracao do modulo health.

Este e o unico controller do projeto que escolhe o status code manualmente
(200 ou 503), porque o resultado "degradado" ainda e uma resposta com corpo util
- nao um erro de dominio.
"""

from fastapi import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.health.repository import HealthRepository
from app.modules.health.schemas import LivenessRead, ReadinessRead
from app.modules.health.service import HealthService


class HealthController:
    def __init__(self, session: AsyncSession) -> None:
        self.service = HealthService(HealthRepository(session))

    def liveness(self) -> LivenessRead:
        return self.service.liveness()

    async def readiness(self, response: Response) -> ReadinessRead:
        result = await self.service.readiness()
        response.status_code = 200 if result.status == "ok" else 503
        return result

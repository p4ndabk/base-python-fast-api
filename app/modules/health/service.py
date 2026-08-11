"""Regra de negocio do health check.

Decisao de design: o readiness NAO lanca excecao quando o banco esta fora. Ele
devolve o diagnostico ("degraded"/"down") e deixa o controller escolher o status
code HTTP - assim o corpo da resposta e util para quem monitora.
"""

import time

from app.core.config import settings
from app.core.logging import get_logger
from app.modules.health.repository import HealthRepository
from app.modules.health.schemas import LivenessRead, ReadinessRead

logger = get_logger(__name__)


class HealthService:
    def __init__(self, repository: HealthRepository) -> None:
        self.repository = repository

    def liveness(self) -> LivenessRead:
        """O processo esta de pe. Nao consulta dependencias."""
        return LivenessRead()

    async def readiness(self) -> ReadinessRead:
        """O processo consegue atender trafego? Depende do banco responder."""
        started = time.perf_counter()
        try:
            await self.repository.ping()
        except Exception as exc:  # noqa: BLE001 - qualquer falha do driver significa "down"
            logger.warning("Health check falhou ao consultar o banco: %s", exc)
            return ReadinessRead(
                status="degraded",
                database="down",
                latency_ms=round((time.perf_counter() - started) * 1000, 2),
                version=settings.app_version,
                environment=settings.environment,
            )

        return ReadinessRead(
            status="ok",
            database="up",
            latency_ms=round((time.perf_counter() - started) * 1000, 2),
            version=settings.app_version,
            environment=settings.environment,
        )

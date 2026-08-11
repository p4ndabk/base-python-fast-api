"""Rotas de health check.

GET /health/live   -> liveness  (Docker/k8s: o container esta vivo?)
GET /health/ready  -> readiness (o app consegue atender? checa o banco de verdade)
"""

from fastapi import APIRouter, Response, status

from app.api.deps import SessionDep
from app.modules.health.controller import HealthController
from app.modules.health.schemas import LivenessRead, ReadinessRead

router = APIRouter(prefix="/health", tags=["health"])


@router.get(
    "/live",
    response_model=LivenessRead,
    status_code=status.HTTP_200_OK,
    summary="Liveness probe",
)
async def liveness(session: SessionDep) -> LivenessRead:
    return HealthController(session).liveness()


@router.get(
    "/ready",
    response_model=ReadinessRead,
    status_code=status.HTTP_200_OK,
    summary="Readiness probe (verifica a conexao com o banco)",
    responses={503: {"model": ReadinessRead, "description": "Alguma dependencia esta fora"}},
)
async def readiness(session: SessionDep, response: Response) -> ReadinessRead:
    return await HealthController(session).readiness(response)

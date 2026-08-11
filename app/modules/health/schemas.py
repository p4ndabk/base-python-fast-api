"""Contratos de entrada/saida do modulo health."""

from typing import Literal

from pydantic import BaseModel, Field


class LivenessRead(BaseModel):
    """Resposta de /health/live - nao toca no banco."""

    status: Literal["ok"] = "ok"


class ReadinessRead(BaseModel):
    """Resposta de /health/ready - reflete o estado real das dependencias."""

    status: Literal["ok", "degraded"]
    database: Literal["up", "down"]
    latency_ms: float = Field(..., description="Tempo do SELECT 1 no banco, em milissegundos")
    version: str
    environment: str

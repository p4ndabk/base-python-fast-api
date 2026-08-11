"""Erros de dominio.

Estes erros sao lancados pela camada de SERVICE e convertidos em resposta HTTP
pelos exception handlers registrados em `app/main.py`.

Por que existem: o service nao pode conhecer HTTP (ver AGENTS.md na raiz). Ele
lanca um erro de dominio; quem traduz para status code e o handler global.
"""

from typing import Any


class AppError(Exception):
    """Base de todo erro de dominio da aplicacao."""

    status_code: int = 400
    code: str = "APP_ERROR"

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class NotFoundError(AppError):
    """Recurso solicitado nao existe. -> HTTP 404"""

    status_code = 404
    code = "NOT_FOUND"


class ConflictError(AppError):
    """Conflito com o estado atual (ex: e-mail ja cadastrado). -> HTTP 409"""

    status_code = 409
    code = "CONFLICT"


class DomainValidationError(AppError):
    """Entrada valida sintaticamente, mas invalida para a regra de negocio. -> HTTP 400"""

    status_code = 400
    code = "VALIDATION_ERROR"


class UnauthorizedError(AppError):
    """Credenciais ausentes ou invalidas. -> HTTP 401"""

    status_code = 401
    code = "UNAUTHORIZED"


class ForbiddenError(AppError):
    """Autenticado, mas sem permissao para a acao. -> HTTP 403"""

    status_code = 403
    code = "FORBIDDEN"


class ServiceUnavailableError(AppError):
    """Dependencia externa (banco, fila) indisponivel. -> HTTP 503"""

    status_code = 503
    code = "SERVICE_UNAVAILABLE"

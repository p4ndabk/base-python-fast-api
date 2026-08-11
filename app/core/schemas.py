"""Schemas compartilhados por todos os modulos: erro e paginacao.

O formato de erro e de pagina e UNICO na API inteira (ver .claude/base_spec.md).
Nao crie variacoes por modulo.
"""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorDetail(BaseModel):
    code: str = Field(..., examples=["NOT_FOUND"])
    message: str = Field(..., examples=["Usuario nao encontrado"])
    details: dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    """Formato unico de erro da API: {"error": {...}} (RN-GLOBAL-004)."""

    error: ErrorDetail


class PageParams(BaseModel):
    """Paginacao padrao. RN-GLOBAL-003: limite maximo de 100 itens por pagina."""

    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class Page(BaseModel, Generic[T]):
    """Envelope unico de listagem."""

    items: list[T]
    total: int
    limit: int
    offset: int

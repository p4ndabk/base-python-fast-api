"""Ponto de entrada da aplicacao.

Responsabilidades deste arquivo (e SO estas):
  1. criar a instancia do FastAPI;
  2. registrar middlewares (CORS);
  3. registrar os exception handlers globais (dominio -> HTTP);
  4. incluir o router agregador de `app/api/v1.py`.

NUNCA declare rotas aqui. Rota vive em `app/modules/<modulo>/router.py`.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1 import api_router
from app.core.config import settings
from app.core.exceptions import AppError
from app.core.logging import get_logger, setup_logging
from app.database.session import engine

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    setup_logging()
    logger.info(
        "Iniciando %s v%s (%s)", settings.app_name, settings.app_version, settings.environment
    )
    yield
    await engine.dispose()
    logger.info("Aplicacao encerrada")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Template base de API FastAPI com arquitetura em camadas.",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    _register_exception_handlers(app)
    app.include_router(api_router)
    return app


def _register_exception_handlers(app: FastAPI) -> None:
    """Traduz erros em respostas no formato unico {"error": {code, message, details}}."""

    @app.exception_handler(AppError)
    async def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message, "details": exc.details}},
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "UNPROCESSABLE_ENTITY",
                    "message": "Dados de entrada invalidos",
                    "details": {"errors": jsonable_errors(exc)},
                }
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": "HTTP_ERROR",
                    "message": str(exc.detail),
                    "details": {},
                }
            },
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("Erro nao tratado: %s", exc)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Erro interno do servidor",
                    "details": {},
                }
            },
        )


def jsonable_errors(exc: RequestValidationError) -> list[dict[str, str]]:
    """Reduz os erros do Pydantic ao essencial (campo + mensagem), sem objetos nao serializaveis."""
    return [
        {"field": ".".join(str(p) for p in err.get("loc", [])), "message": err.get("msg", "")}
        for err in exc.errors()
    ]


app = create_app()

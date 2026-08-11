"""Rotas de autenticacao.

POST /auth/register -> cria a conta
POST /auth/login    -> troca credenciais por um par de tokens
POST /auth/refresh  -> renova o access token
GET  /auth/me       -> dados do usuario autenticado
"""

from fastapi import APIRouter, status

from app.api.deps import CurrentUserDep, SessionDep
from app.core.schemas import ErrorResponse
from app.modules.auth.controller import AuthController
from app.modules.auth.schemas import LoginRequest, RefreshRequest, TokenPair
from app.modules.users.schemas import UserCreate, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Registra um novo usuario",
    responses={409: {"model": ErrorResponse, "description": "E-mail ja cadastrado"}},
)
async def register(data: UserCreate, session: SessionDep) -> UserRead:
    return await AuthController(session).register(data)


@router.post(
    "/login",
    response_model=TokenPair,
    status_code=status.HTTP_200_OK,
    summary="Autentica e devolve access + refresh token",
    responses={401: {"model": ErrorResponse, "description": "Credenciais invalidas"}},
)
async def login(data: LoginRequest, session: SessionDep) -> TokenPair:
    return await AuthController(session).login(data.email, data.password)


@router.post(
    "/refresh",
    response_model=TokenPair,
    status_code=status.HTTP_200_OK,
    summary="Renova os tokens a partir de um refresh token",
    responses={401: {"model": ErrorResponse, "description": "Refresh token invalido ou expirado"}},
)
async def refresh(data: RefreshRequest, session: SessionDep) -> TokenPair:
    return await AuthController(session).refresh(data.refresh_token)


@router.get(
    "/me",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Dados do usuario autenticado",
    responses={401: {"model": ErrorResponse, "description": "Nao autenticado"}},
)
async def me(current_user: CurrentUserDep) -> UserRead:
    return UserRead.model_validate(current_user)

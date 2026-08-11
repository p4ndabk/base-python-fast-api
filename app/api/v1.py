"""Agregador de rotas da API.

Ao criar um modulo novo, o UNICO lugar que precisa ser tocado fora da pasta do
modulo e aqui: importe o router e chame `api_router.include_router(...)`.
"""

from fastapi import APIRouter

from app.modules.auth.router import router as auth_router
from app.modules.health.router import router as health_router
from app.modules.permissions.router import router as permissions_router
from app.modules.roles.router import router as roles_router
from app.modules.users.router import router as users_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(roles_router)
api_router.include_router(permissions_router)
# api_router.include_router(products_router)  # <- proximo modulo entra aqui

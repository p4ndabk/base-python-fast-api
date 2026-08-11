"""Configuracao da aplicacao, carregada de variaveis de ambiente / .env.

Regra: NENHUM outro arquivo do projeto le os.environ diretamente. Tudo passa por
`settings`, para que exista um unico lugar onde as configuracoes sao declaradas.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Aplicacao
    app_name: str = "base-python-fast-api"
    app_version: str = "0.1.0"
    environment: str = "development"

    # Banco de dados (precisa ser um driver async: postgresql+asyncpg)
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/app"
    database_echo: bool = False

    # Auth
    jwt_secret: str = "troque-este-valor-em-producao"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # CORS
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment.lower() in {"production", "prod"}


@lru_cache
def get_settings() -> Settings:
    """Cacheado: as settings sao lidas do ambiente uma unica vez por processo."""
    return Settings()


settings = get_settings()

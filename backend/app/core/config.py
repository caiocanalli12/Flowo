"""Configuração da aplicação, lida de variáveis de ambiente."""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends, Request
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Os valores padrão servem para rodar no host com o Postgres do docker compose.

    O host é `127.0.0.1`, não `localhost`: a porta do compose só escuta em IPv4, e no
    Windows `localhost` tenta `::1` primeiro, o que atrasa cada conexão em ~2 s.
    """

    database_url: str = "postgresql+asyncpg://flowo:flowo@127.0.0.1:5432/flowo"
    test_database_url: str = "postgresql+asyncpg://flowo:flowo@127.0.0.1:5432/flowo_test"
    # Em variável de ambiente, como lista JSON: CORS_ORIGINS='["http://localhost:5173"]'.
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])
    app_version: str = "0.1.0"


@lru_cache
def get_settings() -> Settings:
    return Settings()


def get_app_settings(request: Request) -> Settings:
    """Dependência: as Settings com que a app atual foi criada (os testes usam outras)."""
    settings: Settings = request.app.state.settings
    return settings


SettingsDep = Annotated[Settings, Depends(get_app_settings)]

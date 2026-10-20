"""Fixtures dos testes: banco de testes real (TEST_DATABASE_URL), migrado pelo Alembic.

Os comandos do Alembic rodam via `asyncio.to_thread`, porque o env.py chama `asyncio.run`.
"""

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import Settings, get_settings
from app.core.db import Database
from app.main import create_app

BACKEND_DIR = Path(__file__).resolve().parents[1]

# Porta fechada: a conexão é recusada (ou estoura o timeout do health check).
UNREACHABLE_DATABASE_URL = "postgresql+asyncpg://flowo:flowo@127.0.0.1:1/flowo"


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Settings da app apontando para o banco de testes."""
    settings = get_settings()
    if settings.test_database_url == settings.database_url:
        pytest.exit("TEST_DATABASE_URL must differ from DATABASE_URL: tests truncate tables.")
    return settings.model_copy(update={"database_url": settings.test_database_url})


@pytest.fixture(scope="session")
def alembic_config(test_settings: Settings) -> Config:
    config = Config(BACKEND_DIR / "alembic.ini")
    config.set_main_option("script_location", str(BACKEND_DIR / "migrations"))
    config.attributes["database_url"] = test_settings.database_url
    config.attributes["configure_logger"] = False
    return config


@pytest.fixture(scope="session")
async def migrated_database(alembic_config: Config) -> None:
    """Leva o banco de testes ao head uma vez por sessão."""
    await asyncio.to_thread(command.upgrade, alembic_config, "head")


@pytest.fixture
async def test_engine(test_settings: Settings) -> AsyncIterator[AsyncEngine]:
    """Engine sem pool: não deixa conexões abertas entre testes."""
    engine = create_async_engine(test_settings.database_url, poolclass=NullPool)
    yield engine
    await engine.dispose()


@pytest.fixture
async def empty_database(test_engine: AsyncEngine, migrated_database: None) -> None:
    async with test_engine.begin() as connection:
        await connection.execute(text("TRUNCATE TABLE workflows"))


@asynccontextmanager
async def serve(settings: Settings) -> AsyncIterator[AsyncClient]:
    """Cliente HTTP sobre uma app nova, com o lifespan rodando."""
    app = create_app(settings)
    async with (
        app.router.lifespan_context(app),
        AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http_client,
    ):
        yield http_client


@pytest.fixture
async def client(test_settings: Settings, empty_database: None) -> AsyncIterator[AsyncClient]:
    async with serve(test_settings) as http_client:
        yield http_client


@pytest.fixture
async def client_without_database(test_settings: Settings) -> AsyncIterator[AsyncClient]:
    """Cliente de uma app cujo banco está inacessível."""
    settings = test_settings.model_copy(update={"database_url": UNREACHABLE_DATABASE_URL})
    async with serve(settings) as http_client:
        yield http_client


@pytest.fixture
async def session(test_settings: Settings, empty_database: None) -> AsyncIterator[AsyncSession]:
    database = Database(test_settings.database_url)
    try:
        async with database.sessionmaker() as db_session:
            yield db_session
    finally:
        await database.dispose()

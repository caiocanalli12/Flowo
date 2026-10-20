import asyncio

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncEngine


async def table_names(engine: AsyncEngine) -> list[str]:
    async with engine.connect() as connection:
        return await connection.run_sync(lambda sync: inspect(sync).get_table_names())


async def test_round_trip_downgrade_and_upgrade(
    alembic_config: Config, test_engine: AsyncEngine, migrated_database: None
) -> None:
    await asyncio.to_thread(command.downgrade, alembic_config, "base")
    assert "workflows" not in await table_names(test_engine)

    await asyncio.to_thread(command.upgrade, alembic_config, "head")
    assert "workflows" in await table_names(test_engine)


async def test_models_match_migrations(alembic_config: Config, migrated_database: None) -> None:
    """Equivale a `alembic check`: o autogenerate não pode encontrar diferenças."""
    await asyncio.to_thread(command.check, alembic_config)

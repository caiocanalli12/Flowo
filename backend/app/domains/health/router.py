"""Endpoint de saúde: a API responde e o banco está acessível?"""

import asyncio
import logging

from fastapi import APIRouter, Response, status
from sqlalchemy import text

from app.core.config import SettingsDep
from app.core.db import Database, DatabaseDep
from app.domains.health.schemas import HealthStatus

DATABASE_CHECK_TIMEOUT_SECONDS = 2.0

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["health"])


async def _database_is_reachable(database: Database) -> bool:
    try:
        async with asyncio.timeout(DATABASE_CHECK_TIMEOUT_SECONDS):
            async with database.engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
    except Exception:
        # Qualquer falha (rede, timeout, credenciais, banco inexistente) = indisponível.
        logger.warning("Database health check failed", exc_info=True)
        return False
    return True


@router.get(
    "/health",
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"model": HealthStatus}},
)
async def get_health(
    database: DatabaseDep, settings: SettingsDep, response: Response
) -> HealthStatus:
    if await _database_is_reachable(database):
        return HealthStatus(status="ok", database="ok", version=settings.app_version)
    response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return HealthStatus(status="degraded", database="unavailable", version=settings.app_version)

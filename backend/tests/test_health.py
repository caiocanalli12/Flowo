from fastapi import status
from httpx import AsyncClient

from app.core.config import Settings


async def test_health_ok(client: AsyncClient, test_settings: Settings) -> None:
    response = await client.get("/api/health")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "status": "ok",
        "database": "ok",
        "version": test_settings.app_version,
    }


async def test_health_degraded_when_database_is_unreachable(
    client_without_database: AsyncClient, test_settings: Settings
) -> None:
    response = await client_without_database.get("/api/health")

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert response.json() == {
        "status": "degraded",
        "database": "unavailable",
        "version": test_settings.app_version,
    }

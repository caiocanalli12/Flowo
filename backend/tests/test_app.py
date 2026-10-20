from fastapi import status
from httpx import AsyncClient

from app.core.config import Settings


async def test_openapi_is_served_under_api(client: AsyncClient) -> None:
    response = await client.get("/api/openapi.json")

    assert response.status_code == status.HTTP_200_OK
    schema = response.json()
    paths = schema["paths"].keys()
    assert schema["info"]["title"] == "Flowo API"
    assert {"/api/health", "/api/workflows", "/api/workflows/{workflow_id}"} <= paths
    assert (await client.get("/api/docs")).status_code == status.HTTP_200_OK


async def test_cors_allows_configured_origin(client: AsyncClient, test_settings: Settings) -> None:
    origin = test_settings.cors_origins[0]

    response = await client.options(
        "/api/workflows",
        headers={"Origin": origin, "Access-Control-Request-Method": "POST"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.headers["access-control-allow-origin"] == origin

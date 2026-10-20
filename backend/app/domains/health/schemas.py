"""Contrato do endpoint de saúde."""

from typing import Literal

from app.core.schema import FlowoModel


class HealthStatus(FlowoModel):
    """Resposta de `GET /api/health`.

    `status` é `degraded` quando a API responde mas o banco não.
    """

    status: Literal["ok", "degraded"]
    database: Literal["ok", "unavailable"]
    version: str

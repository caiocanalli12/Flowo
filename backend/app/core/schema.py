"""Base comum dos modelos Pydantic expostos pela API."""

from pydantic import BaseModel, ConfigDict


class FlowoModel(BaseModel):
    """Modelo base do contrato: rejeita campos desconhecidos.

    `extra="forbid"` também faz o JSON Schema exportado declarar
    `additionalProperties: false`, o que gera tipos TypeScript fechados.
    """

    model_config = ConfigDict(extra="forbid")

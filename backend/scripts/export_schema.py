"""Exporta o contrato da API como JSON Schema em `shared/schema/flowo.schema.json`.

Uso: `uv run python -m scripts.export_schema` (ou `make types`, que também
gera os tipos TypeScript do frontend a partir deste arquivo).
"""

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel
from pydantic.json_schema import models_json_schema

from app.domains.health.schemas import HealthStatus
from app.domains.workflows.schemas import (
    Edge,
    EdgeEndpoint,
    Node,
    Position,
    Workflow,
    WorkflowCreate,
    WorkflowSummary,
    WorkflowUpdate,
)

# backend/scripts/ -> raiz do repositório. Nos containers, /app/scripts -> /.
SCHEMA_PATH = Path(__file__).resolve().parents[2] / "shared" / "schema" / "flowo.schema.json"

EXPORTED_MODELS: tuple[type[BaseModel], ...] = (
    Workflow,
    WorkflowSummary,
    WorkflowCreate,
    WorkflowUpdate,
    Node,
    Edge,
    EdgeEndpoint,
    Position,
    HealthStatus,
)


def _strip_field_titles(definitions: dict[str, Any]) -> None:
    """Remove o `title` dos campos e mantém só o dos modelos.

    Sem isso o json-schema-to-typescript cria um alias por campo (`Id1`, `Name2`...).
    """
    for definition in definitions.values():
        for field_schema in definition.get("properties", {}).values():
            field_schema.pop("title", None)


def build_schema() -> dict[str, Any]:
    """Monta um único documento com todos os modelos em `$defs`."""
    _, top_level = models_json_schema(
        [(model, "validation") for model in EXPORTED_MODELS],
        ref_template="#/$defs/{model}",
    )
    definitions: dict[str, Any] = top_level["$defs"]
    _strip_field_titles(definitions)
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "FlowoContract",
        "description": (
            "Contrato da API do Flowo. GERADO a partir dos modelos Pydantic do backend; "
            "não edite à mão (rode `make types`)."
        ),
        "type": "object",
        "properties": {
            model.__name__: {"$ref": f"#/$defs/{model.__name__}"} for model in EXPORTED_MODELS
        },
        "additionalProperties": False,
        "$defs": dict(sorted(definitions.items())),
    }


def render_schema() -> str:
    """Serializa o schema de forma determinística (usado também pelo teste de divergência)."""
    return json.dumps(build_schema(), indent=2, ensure_ascii=False) + "\n"


def main() -> None:
    SCHEMA_PATH.parent.mkdir(parents=True, exist_ok=True)
    SCHEMA_PATH.write_text(render_schema(), encoding="utf-8", newline="\n")
    print(f"JSON Schema escrito em {SCHEMA_PATH}")


if __name__ == "__main__":
    main()

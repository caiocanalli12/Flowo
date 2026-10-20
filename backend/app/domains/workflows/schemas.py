"""Contrato do workflow: fonte única da verdade do modelo de dados do fluxo.

Estes modelos são exportados como JSON Schema para `shared/schema/` e, a partir
dele, viram os tipos TypeScript do frontend (`make types`). Nunca duplique
esses tipos à mão do lado do frontend.
"""

from collections.abc import Sequence
from datetime import datetime
from typing import Annotated, Any, Self
from uuid import UUID

from pydantic import AfterValidator, ConfigDict, Field, StringConstraints, model_validator

from app.core.schema import FlowoModel
from app.domains.nodes.catalog import NODE_SPECS, NodeType

MAX_NODES = 500
MAX_EDGES = 2_000
GRID_LIMIT = 10_000


def _is_unstorable(text: str) -> bool:
    if "\x00" in text:
        return True
    try:
        text.encode("utf-8")
    except UnicodeEncodeError:  # surrogate UTF-16 isolado (ex.: "\ud800" no JSON)
        return True
    return False


def _contains_unstorable_text(value: object) -> bool:
    if isinstance(value, str):
        return _is_unstorable(value)
    if isinstance(value, dict):
        return any(
            _contains_unstorable_text(key) or _contains_unstorable_text(item)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return any(_contains_unstorable_text(item) for item in value)
    return False


def _reject_unstorable_text[T](value: T) -> T:
    """O Postgres não guarda NUL nem surrogates isolados (texto/JSONB): rejeita com 422, não 500."""
    if _contains_unstorable_text(value):
        raise ValueError("NUL characters and unpaired surrogates are not allowed")
    return value


StorableText = AfterValidator(_reject_unstorable_text)

ElementId = Annotated[
    str, StringConstraints(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
]
"""Id de nó/aresta. Gerado pelo cliente, o que facilita a colaboração em tempo real."""

PortName = Annotated[
    str, StringConstraints(min_length=1, max_length=32, pattern=r"^[a-z][a-z0-9_]*$")
]
WorkflowName = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120), StorableText
]
NodeLabel = Annotated[str, Field(max_length=120), StorableText]
NodeConfig = Annotated[
    dict[str, Any],
    Field(description="Configuração específica do tipo de nó (será tipada por tipo no futuro)."),
    StorableText,
]
GridCoordinate = Annotated[int, Field(ge=-GRID_LIMIT, le=GRID_LIMIT)]


class Position(FlowoModel):
    """Posição do nó na grade isométrica, em células inteiras."""

    x: GridCoordinate
    y: GridCoordinate


class Node(FlowoModel):
    """Um passo do fluxo.

    Todos os campos são obrigatórios (`label` pode ser vazio, `config` pode ser `{}`):
    assim o mesmo tipo serve para entrada e resposta, sem campos opcionais no TS.
    """

    id: ElementId
    type: NodeType
    position: Position
    label: NodeLabel
    config: NodeConfig


class EdgeEndpoint(FlowoModel):
    """Uma ponta de aresta: o nó e a porta dele."""

    node_id: ElementId
    port: PortName


class Edge(FlowoModel):
    """Conexão dirigida de uma porta de saída para uma porta de entrada."""

    id: ElementId
    source: EdgeEndpoint
    target: EdgeEndpoint


def graph_problems(nodes: Sequence[Node], edges: Sequence[Edge]) -> list[str]:
    """Lista as violações estruturais do grafo (vazia quando ele é válido)."""
    problems: list[str] = []

    nodes_by_id: dict[str, Node] = {}
    for node in nodes:
        if node.id in nodes_by_id:
            problems.append(f"duplicate node id '{node.id}'")
        nodes_by_id[node.id] = node

    edge_ids: set[str] = set()
    connections: set[tuple[str, str, str, str]] = set()
    for edge in edges:
        if edge.id in edge_ids:
            problems.append(f"duplicate edge id '{edge.id}'")
        edge_ids.add(edge.id)

        source = nodes_by_id.get(edge.source.node_id)
        target = nodes_by_id.get(edge.target.node_id)
        if source is None:
            problems.append(f"edge '{edge.id}': source node '{edge.source.node_id}' not found")
        elif edge.source.port not in NODE_SPECS[source.type].outputs:
            problems.append(
                f"edge '{edge.id}': node type '{source.type}' has no output port "
                f"'{edge.source.port}'"
            )
        if target is None:
            problems.append(f"edge '{edge.id}': target node '{edge.target.node_id}' not found")
        elif edge.target.port not in NODE_SPECS[target.type].inputs:
            problems.append(
                f"edge '{edge.id}': node type '{target.type}' has no input port "
                f"'{edge.target.port}'"
            )

        if edge.source.node_id == edge.target.node_id:
            problems.append(f"edge '{edge.id}': a node cannot connect to itself")

        connection = (
            edge.source.node_id,
            edge.source.port,
            edge.target.node_id,
            edge.target.port,
        )
        if connection in connections:
            problems.append(f"edge '{edge.id}': duplicate connection")
        connections.add(connection)

    return problems


class _WorkflowInput(FlowoModel):
    """Campos editáveis de um workflow, com validação estrutural do grafo."""

    name: WorkflowName
    nodes: list[Node] = Field(max_length=MAX_NODES)
    edges: list[Edge] = Field(max_length=MAX_EDGES)

    @model_validator(mode="after")
    def _validate_graph(self) -> Self:
        problems = graph_problems(self.nodes, self.edges)
        if problems:
            raise ValueError("; ".join(problems))
        return self


class WorkflowCreate(_WorkflowInput):
    """Corpo de `POST /api/workflows`. O grafo pode começar vazio."""

    nodes: list[Node] = Field(default_factory=list, max_length=MAX_NODES)
    edges: list[Edge] = Field(default_factory=list, max_length=MAX_EDGES)


class WorkflowUpdate(_WorkflowInput):
    """Corpo de `PUT /api/workflows/{id}`: substitui nome e grafo por completo."""


class Workflow(FlowoModel):
    """Workflow persistido, como a API o devolve."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    name: str
    nodes: list[Node]
    edges: list[Edge]
    created_at: datetime
    updated_at: datetime


class WorkflowSummary(FlowoModel):
    """Item da listagem: metadados sem o grafo completo."""

    id: UUID
    name: str
    node_count: int = Field(ge=0)
    edge_count: int = Field(ge=0)
    created_at: datetime
    updated_at: datetime

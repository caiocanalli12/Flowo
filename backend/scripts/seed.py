"""Cria um workflow de exemplo no banco de desenvolvimento (idempotente).

Uso: `uv run python -m scripts.seed` (ou `make seed`).
"""

import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.db import Database
from app.domains.nodes.catalog import (
    CONDITION_FALSE_PORT,
    CONDITION_TRUE_PORT,
    DEFAULT_INPUT_PORT,
    DEFAULT_OUTPUT_PORT,
    NodeType,
)
from app.domains.workflows.schemas import Edge, EdgeEndpoint, Node, Position, WorkflowCreate
from app.domains.workflows.service import WorkflowService

EXAMPLE_NAME = "Exemplo: Webhook → HTTP → Condição"


def _edge(edge_id: str, source: str, target: str, source_port: str = DEFAULT_OUTPUT_PORT) -> Edge:
    return Edge(
        id=edge_id,
        source=EdgeEndpoint(node_id=source, port=source_port),
        target=EdgeEndpoint(node_id=target, port=DEFAULT_INPUT_PORT),
    )


def build_example() -> WorkflowCreate:
    """Webhook → HTTP → Condição, que ramifica para e-mail (true) ou LLM (false)."""
    return WorkflowCreate(
        name=EXAMPLE_NAME,
        nodes=[
            Node(
                id="webhook",
                type=NodeType.WEBHOOK,
                position=Position(x=0, y=0),
                label="Pedido recebido",
                config={"method": "POST", "path": "/pedidos"},
            ),
            Node(
                id="fetch_customer",
                type=NodeType.HTTP_REQUEST,
                position=Position(x=4, y=0),
                label="Buscar cliente",
                config={"method": "GET", "url": "https://api.example.com/clientes/{id}"},
            ),
            Node(
                id="is_vip",
                type=NodeType.CONDITION,
                position=Position(x=8, y=0),
                label="Cliente VIP?",
                config={"expression": "customer.tier == 'vip'"},
            ),
            Node(
                id="notify_team",
                type=NodeType.EMAIL,
                position=Position(x=12, y=-3),
                label="Avisar a equipe",
                config={"to": "vendas@example.com"},
            ),
            Node(
                id="draft_reply",
                type=NodeType.LLM,
                position=Position(x=12, y=3),
                label="Rascunhar resposta",
                config={"prompt": "Escreva uma resposta cordial para o pedido."},
            ),
        ],
        edges=[
            _edge("webhook_to_fetch", "webhook", "fetch_customer"),
            _edge("fetch_to_condition", "fetch_customer", "is_vip"),
            _edge("vip_to_email", "is_vip", "notify_team", CONDITION_TRUE_PORT),
            _edge("regular_to_llm", "is_vip", "draft_reply", CONDITION_FALSE_PORT),
        ],
    )


async def seed(session: AsyncSession) -> bool:
    """Cria o exemplo se ainda não existir. Devolve True quando criou."""
    service = WorkflowService(session)
    if any(summary.name == EXAMPLE_NAME for summary in await service.list_summaries()):
        return False
    await service.create(build_example())
    return True


async def _main() -> None:
    database = Database(get_settings().database_url)
    try:
        async with database.sessionmaker() as session:
            created = await seed(session)
    finally:
        await database.dispose()
    if created:
        print(f"Workflow de exemplo criado: {EXAMPLE_NAME!r}")
    else:
        print(f"Workflow de exemplo já existe, nada a fazer: {EXAMPLE_NAME!r}")


if __name__ == "__main__":
    asyncio.run(_main())

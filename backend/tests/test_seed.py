from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.workflows.service import WorkflowService
from scripts.seed import EXAMPLE_NAME, build_example, seed


def test_example_is_a_valid_graph() -> None:
    example = build_example()

    assert [node.type for node in example.nodes] == [
        "webhook",
        "http_request",
        "condition",
        "email",
        "llm",
    ]
    branches = {
        edge.source.port: edge.target.node_id
        for edge in example.edges
        if edge.source.node_id == "is_vip"
    }
    assert branches == {"true": "notify_team", "false": "draft_reply"}


async def test_seed_is_idempotent(session: AsyncSession) -> None:
    assert await seed(session) is True
    assert await seed(session) is False

    summaries = await WorkflowService(session).list_summaries()
    assert [(item.name, item.node_count, item.edge_count) for item in summaries] == [
        (EXAMPLE_NAME, 5, 4)
    ]

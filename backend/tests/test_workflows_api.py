from datetime import datetime
from typing import Any
from uuid import uuid4

import pytest
from fastapi import status
from httpx import AsyncClient

NOT_FOUND = {"detail": "Workflow not found"}


def node(node_id: str, node_type: str, x: int = 0, y: int = 0) -> dict[str, Any]:
    return {
        "id": node_id,
        "type": node_type,
        "position": {"x": x, "y": y},
        "label": "",
        "config": {},
    }


def edge(edge_id: str, source: str, target: str, source_port: str = "out") -> dict[str, Any]:
    return {
        "id": edge_id,
        "source": {"node_id": source, "port": source_port},
        "target": {"node_id": target, "port": "in"},
    }


def simple_graph() -> dict[str, Any]:
    return {
        "nodes": [node("trigger", "manual_trigger"), node("call", "http_request", x=3)],
        "edges": [edge("e1", "trigger", "call")],
    }


async def create(client: AsyncClient, name: str, **body: Any) -> dict[str, Any]:
    response = await client.post("/api/workflows", json={"name": name, **body})
    assert response.status_code == status.HTTP_201_CREATED, response.text
    created: dict[str, Any] = response.json()
    return created


async def test_create_returns_workflow_and_location(client: AsyncClient) -> None:
    response = await client.post("/api/workflows", json={"name": "Primeiro", **simple_graph()})

    assert response.status_code == status.HTTP_201_CREATED
    body = response.json()
    assert body["name"] == "Primeiro"
    assert body["nodes"] == simple_graph()["nodes"]
    assert body["edges"] == simple_graph()["edges"]
    assert body["created_at"] == body["updated_at"]
    assert response.headers["location"] == f"/api/workflows/{body['id']}"

    fetched = await client.get(response.headers["location"])
    assert fetched.status_code == status.HTTP_200_OK
    assert fetched.json() == body


async def test_create_defaults_to_empty_graph_and_strips_name(client: AsyncClient) -> None:
    body = await create(client, "  Vazio  ")

    assert body["name"] == "Vazio"
    assert body["nodes"] == []
    assert body["edges"] == []


async def test_list_orders_by_most_recently_updated_and_counts_in_sql(
    client: AsyncClient,
) -> None:
    first = await create(client, "Primeiro", **simple_graph())
    second = await create(client, "Segundo")

    response = await client.get("/api/workflows")
    assert response.status_code == status.HTTP_200_OK
    assert [item["id"] for item in response.json()] == [second["id"], first["id"]]

    await client.put(f"/api/workflows/{first['id']}", json={"name": "Primeiro", **simple_graph()})

    summaries = (await client.get("/api/workflows")).json()
    assert [item["id"] for item in summaries] == [first["id"], second["id"]]
    assert summaries[0].keys() == {
        "id",
        "name",
        "node_count",
        "edge_count",
        "created_at",
        "updated_at",
    }
    assert (summaries[0]["node_count"], summaries[0]["edge_count"]) == (2, 1)
    assert (summaries[1]["node_count"], summaries[1]["edge_count"]) == (0, 0)


async def test_list_is_empty_without_workflows(client: AsyncClient) -> None:
    response = await client.get("/api/workflows")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


async def test_put_replaces_everything_and_advances_updated_at(client: AsyncClient) -> None:
    created = await create(client, "Antes", **simple_graph())

    response = await client.put(
        f"/api/workflows/{created['id']}",
        json={"name": "Depois", "nodes": [node("only", "webhook")], "edges": []},
    )

    assert response.status_code == status.HTTP_200_OK
    updated = response.json()
    assert updated["id"] == created["id"]
    assert updated["name"] == "Depois"
    assert [item["id"] for item in updated["nodes"]] == ["only"]
    assert updated["edges"] == []
    assert updated["created_at"] == created["created_at"]
    assert datetime.fromisoformat(updated["updated_at"]) > datetime.fromisoformat(
        created["updated_at"]
    )
    assert (await client.get(f"/api/workflows/{created['id']}")).json() == updated


async def test_put_with_same_content_still_advances_updated_at(client: AsyncClient) -> None:
    created = await create(client, "Igual", **simple_graph())

    response = await client.put(
        f"/api/workflows/{created['id']}", json={"name": "Igual", **simple_graph()}
    )

    assert datetime.fromisoformat(response.json()["updated_at"]) > datetime.fromisoformat(
        created["updated_at"]
    )


async def test_delete_removes_workflow(client: AsyncClient) -> None:
    created = await create(client, "Descartável")

    response = await client.delete(f"/api/workflows/{created['id']}")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert response.content == b""
    missing = await client.get(f"/api/workflows/{created['id']}")
    assert missing.status_code == status.HTTP_404_NOT_FOUND
    assert (await client.get("/api/workflows")).json() == []


@pytest.mark.parametrize(
    ("method", "body"),
    [
        ("GET", None),
        ("PUT", {"name": "Fantasma", "nodes": [], "edges": []}),
        ("DELETE", None),
    ],
)
async def test_unknown_workflow_returns_404(
    client: AsyncClient, method: str, body: dict[str, Any] | None
) -> None:
    response = await client.request(method, f"/api/workflows/{uuid4()}", json=body)

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == NOT_FOUND


async def test_invalid_uuid_returns_422(client: AsyncClient) -> None:
    response = await client.get("/api/workflows/not-a-uuid")

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


@pytest.mark.parametrize(
    "body",
    [
        pytest.param({"name": "   "}, id="blank-name"),
        pytest.param({"name": "x" * 121}, id="name-too-long"),
        pytest.param({"name": "Extra", "owner": "eu"}, id="extra-field"),
        pytest.param(
            {"name": "Extra", "nodes": [{**node("a", "webhook"), "color": "red"}]},
            id="extra-node-field",
        ),
        pytest.param({"name": "Tipo", "nodes": [node("a", "teleport")]}, id="unknown-node-type"),
        pytest.param(
            {
                "name": "Sem rótulo",
                "nodes": [{"id": "a", "type": "webhook", "position": {"x": 0, "y": 0}}],
            },
            id="node-without-label-and-config",
        ),
        pytest.param({"name": "Nulo\x00"}, id="nul-in-name"),
        pytest.param(
            {"name": "Nulo", "nodes": [{**node("a", "webhook"), "label": "a\x00b"}]},
            id="nul-in-label",
        ),
        pytest.param(
            {"name": "Nulo", "nodes": [{**node("a", "webhook"), "config": {"k": ["ok", "\x00"]}}]},
            id="nul-in-config-value",
        ),
        pytest.param(
            {"name": "Nulo", "nodes": [{**node("a", "webhook"), "config": {"\x00": 1}}]},
            id="nul-in-config-key",
        ),
        pytest.param(
            {"name": "Órfã", "nodes": [node("a", "webhook")], "edges": [edge("e", "a", "b")]},
            id="edge-to-missing-node",
        ),
    ],
)
async def test_create_rejects_invalid_body(client: AsyncClient, body: dict[str, Any]) -> None:
    response = await client.post("/api/workflows", json=body)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert (await client.get("/api/workflows")).json() == []


def raw_workflow_with_node(label: str = '""', config: str = "{}") -> str:
    """JSON cru de um workflow com um nó, para enviar escapes que o httpx não codifica."""
    node_json = (
        '{"id":"a","type":"webhook","position":{"x":0,"y":0},'
        f'"label":{label},"config":{config}}}'
    )
    return f'{{"name":"x","nodes":[{node_json}]}}'


@pytest.mark.parametrize(
    "raw_body",
    [
        pytest.param('{"name":"\\ud800"}', id="name"),
        pytest.param(raw_workflow_with_node(label='"\\ud800"'), id="label"),
        pytest.param(raw_workflow_with_node(config='{"v":"\\ud800"}'), id="config-value"),
        pytest.param(raw_workflow_with_node(config='{"a":{"\\ud800":1}}'), id="config-nested-key"),
    ],
)
async def test_create_rejects_unpaired_surrogates_with_422(
    client: AsyncClient, raw_body: str
) -> None:
    # JSON cru: o `json=` do httpx não consegue codificar um surrogate isolado.
    response = await client.post(
        "/api/workflows",
        content=raw_body.encode("ascii"),
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert (await client.get("/api/workflows")).json() == []


async def test_put_rejects_invalid_graph_and_keeps_stored_workflow(client: AsyncClient) -> None:
    created = await create(client, "Intacto", **simple_graph())

    response = await client.put(
        f"/api/workflows/{created['id']}",
        json={
            "name": "Quebrado",
            "nodes": [node("trigger", "webhook"), node("call", "http_request")],
            "edges": [edge("e1", "call", "trigger")],
        },
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert "has no input port 'in'" in response.text
    assert (await client.get(f"/api/workflows/{created['id']}")).json() == created


async def test_put_requires_full_body(client: AsyncClient) -> None:
    created = await create(client, "Completo")

    response = await client.put(f"/api/workflows/{created['id']}", json={"name": "Só nome"})

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

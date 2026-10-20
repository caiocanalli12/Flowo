import pytest
from pydantic import ValidationError

from app.domains.nodes.catalog import NodeType
from app.domains.workflows.schemas import (
    Edge,
    EdgeEndpoint,
    Node,
    Position,
    WorkflowCreate,
    WorkflowUpdate,
    graph_problems,
)


def node(node_id: str, node_type: NodeType) -> Node:
    return Node(id=node_id, type=node_type, position=Position(x=0, y=0), label="", config={})


def edge(
    edge_id: str, source: str, target: str, source_port: str = "out", target_port: str = "in"
) -> Edge:
    return Edge(
        id=edge_id,
        source=EdgeEndpoint(node_id=source, port=source_port),
        target=EdgeEndpoint(node_id=target, port=target_port),
    )


TRIGGER = node("trigger", NodeType.WEBHOOK)
ACTION = node("action", NodeType.HTTP_REQUEST)
OTHER_ACTION = node("other", NodeType.EMAIL)
CONDITION = node("check", NodeType.CONDITION)


def test_valid_graph_has_no_problems() -> None:
    nodes = [TRIGGER, ACTION, CONDITION, OTHER_ACTION, node("llm", NodeType.LLM)]
    edges = [
        edge("e1", "trigger", "action"),
        edge("e2", "action", "check"),
        edge("e3", "check", "other", source_port="true"),
        edge("e4", "check", "llm", source_port="false"),
    ]

    assert graph_problems(nodes, edges) == []


def test_empty_graph_is_valid() -> None:
    assert graph_problems([], []) == []


def test_duplicate_node_ids() -> None:
    assert graph_problems([TRIGGER, node("trigger", NodeType.SCHEDULE)], []) == [
        "duplicate node id 'trigger'"
    ]


def test_duplicate_edge_ids() -> None:
    edges = [edge("e1", "trigger", "action"), edge("e1", "trigger", "other")]

    assert graph_problems([TRIGGER, ACTION, OTHER_ACTION], edges) == ["duplicate edge id 'e1'"]


def test_edge_to_missing_nodes() -> None:
    assert graph_problems([], [edge("e1", "ghost", "phantom")]) == [
        "edge 'e1': source node 'ghost' not found",
        "edge 'e1': target node 'phantom' not found",
    ]


def test_wrong_output_port() -> None:
    edges = [edge("e1", "action", "other", source_port="true")]

    assert graph_problems([ACTION, OTHER_ACTION], edges) == [
        "edge 'e1': node type 'http_request' has no output port 'true'"
    ]


def test_wrong_input_port() -> None:
    edges = [edge("e1", "action", "other", target_port="payload")]

    assert graph_problems([ACTION, OTHER_ACTION], edges) == [
        "edge 'e1': node type 'email' has no input port 'payload'"
    ]


def test_trigger_cannot_be_a_target() -> None:
    assert graph_problems([TRIGGER, ACTION], [edge("e1", "action", "trigger")]) == [
        "edge 'e1': node type 'webhook' has no input port 'in'"
    ]


def test_condition_exposes_only_true_and_false() -> None:
    nodes = [CONDITION, ACTION, OTHER_ACTION]
    valid = [
        edge("e1", "check", "action", source_port="true"),
        edge("e2", "check", "other", source_port="false"),
    ]

    assert graph_problems(nodes, valid) == []
    assert graph_problems(nodes, [edge("e3", "check", "action")]) == [
        "edge 'e3': node type 'condition' has no output port 'out'"
    ]


def test_self_loop() -> None:
    assert graph_problems([ACTION], [edge("e1", "action", "action")]) == [
        "edge 'e1': a node cannot connect to itself"
    ]


def test_duplicate_connection() -> None:
    edges = [edge("e1", "trigger", "action"), edge("e2", "trigger", "action")]

    assert graph_problems([TRIGGER, ACTION], edges) == ["edge 'e2': duplicate connection"]


def test_workflow_input_strips_name() -> None:
    assert WorkflowCreate(name="  Meu fluxo \n").name == "Meu fluxo"


@pytest.mark.parametrize("name", ["", "   "])
def test_workflow_input_rejects_empty_name(name: str) -> None:
    with pytest.raises(ValidationError):
        WorkflowCreate(name=name)


def test_workflow_input_reports_graph_problems() -> None:
    with pytest.raises(ValidationError, match="a node cannot connect to itself"):
        WorkflowUpdate(name="Laço", nodes=[ACTION], edges=[edge("e1", "action", "action")])


@pytest.mark.parametrize(
    "overrides",
    [
        pytest.param({"label": "a\x00"}, id="label"),
        pytest.param({"config": {"nested": {"deep": ["\x00"]}}}, id="config-value"),
        pytest.param({"config": {"ke\x00y": 1}}, id="config-key"),
        pytest.param({"config": {"k": "\ud800"}}, id="config-surrogate-value"),
        pytest.param({"config": {"a": {"\udfff": 1}}}, id="config-surrogate-key"),
    ],
)
def test_node_rejects_unstorable_text(overrides: dict[str, object]) -> None:
    data = {"id": "n", "type": "webhook", "position": {"x": 0, "y": 0}, "label": "", "config": {}}

    with pytest.raises(ValidationError, match="NUL characters and unpaired surrogates"):
        Node.model_validate({**data, **overrides})


def test_node_requires_label_and_config() -> None:
    with pytest.raises(ValidationError) as error:
        Node.model_validate({"id": "n", "type": "webhook", "position": {"x": 0, "y": 0}})

    assert {item["loc"][0] for item in error.value.errors()} == {"label", "config"}


def test_workflow_input_rejects_nul_in_name() -> None:
    with pytest.raises(ValidationError, match="NUL characters and unpaired surrogates"):
        WorkflowCreate(name="Fluxo\x00")


def test_workflow_input_forbids_extra_fields() -> None:
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        WorkflowCreate.model_validate({"name": "Fluxo", "owner": "eu"})

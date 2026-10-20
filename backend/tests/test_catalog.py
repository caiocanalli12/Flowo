import pytest

from app.domains.nodes.catalog import NODE_SPECS, NodeCategory, NodeType


def test_every_node_type_has_a_spec() -> None:
    assert set(NODE_SPECS) == set(NodeType)


@pytest.mark.parametrize("node_type", list(NodeType))
def test_ports_follow_category(node_type: NodeType) -> None:
    spec = NODE_SPECS[node_type]

    match spec.category:
        case NodeCategory.TRIGGER:
            assert (spec.inputs, spec.outputs) == ((), ("out",))
        case NodeCategory.ACTION:
            assert (spec.inputs, spec.outputs) == (("in",), ("out",))
        case NodeCategory.LOGIC:
            assert (spec.inputs, spec.outputs) == (("in",), ("true", "false"))


def test_categories() -> None:
    triggers = {t for t, spec in NODE_SPECS.items() if spec.category is NodeCategory.TRIGGER}

    assert triggers == {NodeType.MANUAL_TRIGGER, NodeType.WEBHOOK, NodeType.SCHEDULE}
    assert NODE_SPECS[NodeType.CONDITION].category is NodeCategory.LOGIC

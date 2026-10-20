"""Catálogo dos tipos de nó: identidade, categoria e portas de cada tipo.

Para adicionar um tipo de nó: inclua-o em `NodeType`, registre o `NodeSpec`
em `NODE_SPECS` e rode `make types` para propagar ao frontend.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType


class NodeType(StrEnum):
    """Tipos de nó suportados por um workflow."""

    MANUAL_TRIGGER = "manual_trigger"
    WEBHOOK = "webhook"
    SCHEDULE = "schedule"
    HTTP_REQUEST = "http_request"
    PYTHON_SCRIPT = "python_script"
    JS_SCRIPT = "js_script"
    EMAIL = "email"
    CONDITION = "condition"
    LLM = "llm"


class NodeCategory(StrEnum):
    TRIGGER = "trigger"
    ACTION = "action"
    LOGIC = "logic"


DEFAULT_INPUT_PORT = "in"
DEFAULT_OUTPUT_PORT = "out"
CONDITION_TRUE_PORT = "true"
CONDITION_FALSE_PORT = "false"


@dataclass(frozen=True, slots=True)
class NodeSpec:
    """Forma de um tipo de nó: em quais portas ele recebe e emite dados."""

    category: NodeCategory
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]


_TRIGGER = NodeSpec(NodeCategory.TRIGGER, inputs=(), outputs=(DEFAULT_OUTPUT_PORT,))
_ACTION = NodeSpec(
    NodeCategory.ACTION, inputs=(DEFAULT_INPUT_PORT,), outputs=(DEFAULT_OUTPUT_PORT,)
)
_CONDITION = NodeSpec(
    NodeCategory.LOGIC,
    inputs=(DEFAULT_INPUT_PORT,),
    outputs=(CONDITION_TRUE_PORT, CONDITION_FALSE_PORT),
)

NODE_SPECS: Mapping[NodeType, NodeSpec] = MappingProxyType(
    {
        NodeType.MANUAL_TRIGGER: _TRIGGER,
        NodeType.WEBHOOK: _TRIGGER,
        NodeType.SCHEDULE: _TRIGGER,
        NodeType.HTTP_REQUEST: _ACTION,
        NodeType.PYTHON_SCRIPT: _ACTION,
        NodeType.JS_SCRIPT: _ACTION,
        NodeType.EMAIL: _ACTION,
        NodeType.LLM: _ACTION,
        NodeType.CONDITION: _CONDITION,
    }
)

_missing = set(NodeType) - NODE_SPECS.keys()
if _missing:  # pragma: no cover - falha de configuração detectada no import
    raise RuntimeError(f"NodeType without NodeSpec: {sorted(_missing)}")

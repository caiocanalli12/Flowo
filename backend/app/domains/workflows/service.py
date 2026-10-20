"""Casos de uso de workflows: traduzem entre o contrato Pydantic e a persistência."""

from collections.abc import Sequence
from typing import Any
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.workflows.repository import WorkflowRepository
from app.domains.workflows.schemas import (
    Workflow,
    WorkflowCreate,
    WorkflowSummary,
    WorkflowUpdate,
)


class WorkflowNotFoundError(Exception):
    def __init__(self, workflow_id: UUID) -> None:
        super().__init__(f"Workflow {workflow_id} not found")
        self.workflow_id = workflow_id


def _to_json(items: Sequence[BaseModel]) -> list[dict[str, Any]]:
    return [item.model_dump(mode="json") for item in items]


class WorkflowService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repository = WorkflowRepository(session)

    async def list_summaries(self) -> list[WorkflowSummary]:
        return await self._repository.list_summaries()

    async def get(self, workflow_id: UUID) -> Workflow:
        record = await self._repository.get(workflow_id)
        if record is None:
            raise WorkflowNotFoundError(workflow_id)
        return Workflow.model_validate(record)

    async def create(self, data: WorkflowCreate) -> Workflow:
        record = await self._repository.add(
            name=data.name, nodes=_to_json(data.nodes), edges=_to_json(data.edges)
        )
        await self._session.commit()
        return Workflow.model_validate(record)

    async def update(self, workflow_id: UUID, data: WorkflowUpdate) -> Workflow:
        record = await self._repository.update(
            workflow_id, name=data.name, nodes=_to_json(data.nodes), edges=_to_json(data.edges)
        )
        if record is None:
            raise WorkflowNotFoundError(workflow_id)
        await self._session.commit()
        return Workflow.model_validate(record)

    async def delete(self, workflow_id: UUID) -> None:
        if not await self._repository.delete(workflow_id):
            raise WorkflowNotFoundError(workflow_id)
        await self._session.commit()

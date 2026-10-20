"""Acesso a dados de workflows. Não faz commit: isso é papel do serviço."""

from typing import Any
from uuid import UUID

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.workflows.models import WorkflowRecord
from app.domains.workflows.schemas import WorkflowSummary

type JsonList = list[dict[str, Any]]


class WorkflowRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_summaries(self) -> list[WorkflowSummary]:
        """Metadados de todos os workflows, mais recentes primeiro, sem carregar os grafos."""
        statement = select(
            WorkflowRecord.id,
            WorkflowRecord.name,
            func.jsonb_array_length(WorkflowRecord.nodes).label("node_count"),
            func.jsonb_array_length(WorkflowRecord.edges).label("edge_count"),
            WorkflowRecord.created_at,
            WorkflowRecord.updated_at,
        ).order_by(WorkflowRecord.updated_at.desc(), WorkflowRecord.id)
        result = await self._session.execute(statement)
        return [WorkflowSummary.model_validate(row, from_attributes=True) for row in result]

    async def get(self, workflow_id: UUID) -> WorkflowRecord | None:
        return await self._session.get(WorkflowRecord, workflow_id)

    async def add(self, *, name: str, nodes: JsonList, edges: JsonList) -> WorkflowRecord:
        record = WorkflowRecord(name=name, nodes=nodes, edges=edges)
        self._session.add(record)
        await self._session.flush()
        return record

    async def update(
        self, workflow_id: UUID, *, name: str, nodes: JsonList, edges: JsonList
    ) -> WorkflowRecord | None:
        """Substitui nome e grafo; `updated_at` avança pelo `onupdate` da coluna."""
        statement = (
            update(WorkflowRecord)
            .where(WorkflowRecord.id == workflow_id)
            .values(name=name, nodes=nodes, edges=edges)
            .returning(WorkflowRecord)
        )
        return await self._session.scalar(statement)

    async def delete(self, workflow_id: UUID) -> bool:
        """Remove o workflow; devolve False se ele não existia."""
        statement = (
            delete(WorkflowRecord)
            .where(WorkflowRecord.id == workflow_id)
            .returning(WorkflowRecord.id)
        )
        return await self._session.scalar(statement) is not None

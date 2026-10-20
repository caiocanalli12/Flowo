"""CRUD HTTP de workflows em `/api/workflows`."""

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from app.core.db import SessionDep
from app.domains.workflows.schemas import (
    Workflow,
    WorkflowCreate,
    WorkflowSummary,
    WorkflowUpdate,
)
from app.domains.workflows.service import WorkflowNotFoundError, WorkflowService

NOT_FOUND_DETAIL = "Workflow not found"
NOT_FOUND_RESPONSES: dict[int | str, dict[str, Any]] = {
    status.HTTP_404_NOT_FOUND: {"description": NOT_FOUND_DETAIL}
}

router = APIRouter(prefix="/api/workflows", tags=["workflows"])


def get_workflow_service(session: SessionDep) -> WorkflowService:
    return WorkflowService(session)


ServiceDep = Annotated[WorkflowService, Depends(get_workflow_service)]


def _not_found() -> HTTPException:
    return HTTPException(status.HTTP_404_NOT_FOUND, detail=NOT_FOUND_DETAIL)


@router.get("")
async def list_workflows(service: ServiceDep) -> list[WorkflowSummary]:
    return await service.list_summaries()


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_workflow(
    data: WorkflowCreate, service: ServiceDep, request: Request, response: Response
) -> Workflow:
    workflow = await service.create(data)
    response.headers["Location"] = request.app.url_path_for(
        "get_workflow", workflow_id=str(workflow.id)
    )
    return workflow


@router.get("/{workflow_id}", responses=NOT_FOUND_RESPONSES)
async def get_workflow(workflow_id: UUID, service: ServiceDep) -> Workflow:
    try:
        return await service.get(workflow_id)
    except WorkflowNotFoundError:
        raise _not_found() from None


@router.put("/{workflow_id}", responses=NOT_FOUND_RESPONSES)
async def update_workflow(workflow_id: UUID, data: WorkflowUpdate, service: ServiceDep) -> Workflow:
    try:
        return await service.update(workflow_id, data)
    except WorkflowNotFoundError:
        raise _not_found() from None


@router.delete(
    "/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT, responses=NOT_FOUND_RESPONSES
)
async def delete_workflow(workflow_id: UUID, service: ServiceDep) -> None:
    try:
        await service.delete(workflow_id)
    except WorkflowNotFoundError:
        raise _not_found() from None

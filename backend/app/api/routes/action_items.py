from typing import Literal

from fastapi import APIRouter, Depends, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.action_item import ActionItemCreate, ActionItemOut, ActionItemUpdate
from app.services.action_item_service import ActionItemService

router = APIRouter(tags=["action-items"])


@router.get("/meetings/{meeting_id}/action-items", response_model=list[ActionItemOut])
def list_items(meeting_id: int, status: Literal["TODO", "IN_PROGRESS", "DONE"] | None = None,
               assignee: str | None = None, db: Session = Depends(get_db)):
    return ActionItemService(db).list(meeting_id, status, assignee)


@router.post("/meetings/{meeting_id}/action-items", response_model=ActionItemOut, status_code=201)
def create_item(meeting_id: int, payload: ActionItemCreate, db: Session = Depends(get_db)):
    return ActionItemService(db).create(meeting_id, payload)


@router.patch("/action-items/{item_id}", response_model=ActionItemOut)
def update_item(item_id: int, payload: ActionItemUpdate, db: Session = Depends(get_db)):
    return ActionItemService(db).update(item_id, payload)


@router.delete("/action-items/{item_id}", status_code=204)
def delete_item(item_id: int, db: Session = Depends(get_db)):
    ActionItemService(db).delete(item_id)
    return Response(status_code=204)

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas._base import CleanStr, ORMModel

Status = Literal["TODO", "IN_PROGRESS", "DONE"]


class ActionItemCreate(BaseModel):
    title: CleanStr = Field(min_length=1, max_length=300)
    description: CleanStr | None = Field(default=None, max_length=2000)
    assignee: CleanStr | None = Field(default=None, max_length=120)
    due_date: date | None = None
    status: Status = "TODO"


class ActionItemUpdate(BaseModel):
    title: CleanStr | None = Field(default=None, min_length=1, max_length=300)
    description: CleanStr | None = Field(default=None, max_length=2000)
    assignee: CleanStr | None = Field(default=None, max_length=120)
    due_date: date | None = None
    status: Status | None = None


class ActionItemOut(ORMModel):
    id: int
    meeting_id: int
    title: str
    description: str | None
    assignee: str | None
    due_date: date | None
    status: str
    created_at: datetime
    updated_at: datetime

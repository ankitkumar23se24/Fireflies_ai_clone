from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.schemas._base import CleanStr, ORMModel
from app.schemas.action_item import ActionItemOut


class ParticipantIn(BaseModel):
    name: CleanStr = Field(min_length=1, max_length=120)
    email: CleanStr | None = Field(default=None, max_length=255)
    role: CleanStr | None = Field(default=None, max_length=80)


class ParticipantOut(ORMModel):
    id: int
    name: str
    email: str | None
    role: str | None


class TopicOut(ORMModel):
    id: int
    name: str
    start_time: float
    end_time: float


class ChapterOut(ORMModel):
    id: int
    title: str
    summary: str
    start_time: float
    end_time: float


class SummaryOut(ORMModel):
    overview: str
    key_takeaways: list[str]
    decisions: list[str]
    follow_ups: list[str]
    generated_by: str
    generated_at: datetime


class TagOut(ORMModel):
    id: int
    name: str


class SegmentIn(BaseModel):
    speaker: CleanStr = Field(min_length=1, max_length=120)
    start_time: float = Field(ge=0)
    end_time: float | None = Field(default=None, ge=0)
    text: CleanStr = Field(min_length=1, max_length=5000)


class MeetingCreate(BaseModel):
    title: CleanStr = Field(min_length=1, max_length=200)
    description: CleanStr | None = Field(default=None, max_length=2000)
    date: datetime | None = None
    duration_seconds: int | None = Field(default=None, ge=0, le=60 * 60 * 24)
    media_url: CleanStr | None = Field(default=None, max_length=500)
    tags: list[CleanStr] = Field(default_factory=list, max_length=12)
    participants: list[ParticipantIn] = Field(default_factory=list, max_length=50)
    transcript_text: str | None = Field(default=None, max_length=2_000_000)
    transcript_format: Literal["auto", "txt", "vtt", "json"] = "auto"
    segments: list[SegmentIn] | None = Field(default=None, max_length=5000)

    @field_validator("tags")
    @classmethod
    def _tags(cls, v: list[str]) -> list[str]:
        seen, out = set(), []
        for t in v:
            if t and t.lower() not in seen:
                seen.add(t.lower())
                out.append(t[:50])
        return out


class MeetingUpdate(BaseModel):
    title: CleanStr | None = Field(default=None, min_length=1, max_length=200)
    description: CleanStr | None = Field(default=None, max_length=2000)
    date: datetime | None = None
    duration_seconds: int | None = Field(default=None, ge=0, le=60 * 60 * 24)
    media_url: CleanStr | None = Field(default=None, max_length=500)
    status: Literal["PROCESSING", "COMPLETED", "FAILED"] | None = None
    tags: list[CleanStr] | None = Field(default=None, max_length=12)


class MeetingListItem(ORMModel):
    id: int
    title: str
    description: str | None
    date: datetime
    duration_seconds: int
    status: str
    participants: list[ParticipantOut]
    tags: list[TagOut]
    summary_preview: str | None = None
    action_item_count: int = 0


class MeetingDetail(ORMModel):
    id: int
    title: str
    description: str | None
    date: datetime
    duration_seconds: int
    media_url: str | None
    status: str
    created_at: datetime
    updated_at: datetime
    participants: list[ParticipantOut]
    tags: list[TagOut]
    summary: SummaryOut | None
    topics: list[TopicOut]
    chapters: list[ChapterOut]
    action_items: list[ActionItemOut]


class Page(BaseModel):
    items: list[MeetingListItem]
    total: int
    page: int
    page_size: int


class FilterOptions(BaseModel):
    participants: list[str]
    tags: list[str]

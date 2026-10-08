from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.schemas._base import CleanStr, ORMModel
from app.schemas.meeting import SegmentIn


class CommentOut(ORMModel):
    id: int
    meeting_id: int
    transcript_segment_id: int
    text: str
    author: str
    created_at: datetime


class HighlightOut(ORMModel):
    id: int
    meeting_id: int
    transcript_segment_id: int
    color: str
    note: str | None
    created_at: datetime


class SegmentOut(BaseModel):
    id: int
    meeting_id: int
    participant_id: int | None
    speaker: str
    start_time: float
    end_time: float
    text: str
    sequence_number: int
    comments: list[CommentOut] = []
    highlights: list[HighlightOut] = []


class TranscriptOut(BaseModel):
    meeting_id: int
    segments: list[SegmentOut]
    speakers: list[str]


class TranscriptImport(BaseModel):
    """Replace/append a meeting transcript from raw text (txt/vtt/json) or structured segments."""

    text: str | None = Field(default=None, max_length=2_000_000)
    segments: list[SegmentIn] | None = Field(default=None, max_length=5000)
    format: str = Field(default="auto", pattern="^(auto|txt|vtt|json)$")
    mode: str = Field(default="replace", pattern="^(replace|append)$")

    @model_validator(mode="after")
    def _has_content(self):
        if not (self.text and self.text.strip()) and not self.segments:
            raise ValueError("Provide either 'text' or 'segments'")
        return self


class SegmentUpdate(BaseModel):
    text: CleanStr | None = Field(default=None, min_length=1, max_length=5000)
    speaker: CleanStr | None = Field(default=None, min_length=1, max_length=120)
    start_time: float | None = Field(default=None, ge=0)
    end_time: float | None = Field(default=None, ge=0)

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas._base import CleanStr

Color = Literal["yellow", "green", "blue", "pink", "purple"]


class CommentCreate(BaseModel):
    transcript_segment_id: int
    text: CleanStr = Field(min_length=1, max_length=2000)


class HighlightCreate(BaseModel):
    transcript_segment_id: int
    color: Color = "yellow"
    note: CleanStr | None = Field(default=None, max_length=2000)


class HighlightUpdate(BaseModel):
    color: Color | None = None
    note: CleanStr | None = Field(default=None, max_length=2000)

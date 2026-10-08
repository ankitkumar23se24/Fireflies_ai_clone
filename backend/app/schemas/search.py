from pydantic import BaseModel, Field


class SearchHit(BaseModel):
    type: str  # title | participant | transcript | summary | action_item | topic
    meeting_id: int
    meeting_title: str
    meeting_date: str
    text: str
    timestamp: float | None = None
    segment_id: int | None = None
    participant: str | None = None


class SearchResults(BaseModel):
    query: str
    total: int
    hits: list[SearchHit]


class AskRequest(BaseModel):
    question: str = Field(min_length=2, max_length=500)


class Citation(BaseModel):
    segment_id: int
    timestamp: float
    speaker: str
    text: str


class AskResponse(BaseModel):
    answer: str
    citations: list[Citation]
    provider: str

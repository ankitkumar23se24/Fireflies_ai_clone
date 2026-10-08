"""Comments and highlights on transcript segments. Segment ids are verified against the meeting."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models import Comment, Highlight
from app.repositories.transcript_repository import TranscriptRepository
from app.schemas.comment import CommentCreate, HighlightCreate, HighlightUpdate
from app.services.meeting_service import MeetingService

AUTHOR = "Demo User"


class CollaborationService:
    def __init__(self, db: Session):
        self.db = db
        self.segments = TranscriptRepository(db)

    def _check(self, meeting_id: int, segment_id: int) -> None:
        MeetingService(self.db).get_or_404(meeting_id, detail=False)
        if not self.segments.get_in_meeting(meeting_id, segment_id):
            raise NotFoundError(f"Segment {segment_id} does not belong to meeting {meeting_id}")

    def list_comments(self, meeting_id: int) -> list[Comment]:
        MeetingService(self.db).get_or_404(meeting_id, detail=False)
        return list(self.db.scalars(select(Comment).where(Comment.meeting_id == meeting_id).order_by(Comment.id)).all())

    def add_comment(self, meeting_id: int, payload: CommentCreate) -> Comment:
        self._check(meeting_id, payload.transcript_segment_id)
        c = Comment(meeting_id=meeting_id, transcript_segment_id=payload.transcript_segment_id, text=payload.text, author=AUTHOR)
        self.db.add(c)
        self.db.commit()
        return c

    def delete_comment(self, comment_id: int) -> None:
        c = self.db.get(Comment, comment_id)
        if not c:
            raise NotFoundError(f"Comment {comment_id} not found")
        self.db.delete(c)
        self.db.commit()

    def list_highlights(self, meeting_id: int) -> list[Highlight]:
        MeetingService(self.db).get_or_404(meeting_id, detail=False)
        return list(self.db.scalars(select(Highlight).where(Highlight.meeting_id == meeting_id).order_by(Highlight.id)).all())

    def add_highlight(self, meeting_id: int, payload: HighlightCreate) -> Highlight:
        self._check(meeting_id, payload.transcript_segment_id)
        h = Highlight(meeting_id=meeting_id, transcript_segment_id=payload.transcript_segment_id, color=payload.color, note=payload.note)
        self.db.add(h)
        self.db.commit()
        return h

    def update_highlight(self, highlight_id: int, payload: HighlightUpdate) -> Highlight:
        h = self.db.get(Highlight, highlight_id)
        if not h:
            raise NotFoundError(f"Highlight {highlight_id} not found")
        for k, v in payload.model_dump(exclude_unset=True).items():
            setattr(h, k, v)
        self.db.commit()
        return h

    def delete_highlight(self, highlight_id: int) -> None:
        h = self.db.get(Highlight, highlight_id)
        if not h:
            raise NotFoundError(f"Highlight {highlight_id} not found")
        self.db.delete(h)
        self.db.commit()

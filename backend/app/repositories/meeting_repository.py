"""Data access for meetings. Only place that knows how meeting list filters become SQL."""
from datetime import datetime

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models import ActionItem, Meeting, MeetingTag, Participant, TranscriptSegment
from app.repositories.transcript_repository import like_pattern, matching_segment_ids


def detail_options():
    return (
        selectinload(Meeting.participants), selectinload(Meeting.tags), selectinload(Meeting.summary),
        selectinload(Meeting.topics), selectinload(Meeting.chapters), selectinload(Meeting.action_items),
    )


class MeetingRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, meeting_id: int, detail: bool = True) -> Meeting | None:
        stmt = select(Meeting).where(Meeting.id == meeting_id)
        if detail:
            stmt = stmt.options(*detail_options())
        return self.db.scalars(stmt).first()

    def find(self, *, q: str | None, participant: str | None, tag: str | None, date_from: datetime | None,
             date_to: datetime | None, sort: str, page: int, page_size: int) -> tuple[list[Meeting], int]:
        stmt = select(Meeting)
        if q:
            seg_meeting_ids = select(TranscriptSegment.meeting_id).where(
                TranscriptSegment.id.in_(matching_segment_ids(self.db, q, limit=500))
            )
            pat = like_pattern(q)
            stmt = stmt.where(or_(
                Meeting.title.ilike(pat, escape="\\"),
                Meeting.id.in_(select(Participant.meeting_id).where(Participant.name.ilike(pat, escape="\\"))),
                Meeting.id.in_(seg_meeting_ids),
            ))
        if participant:
            stmt = stmt.where(Meeting.id.in_(select(Participant.meeting_id).where(Participant.name == participant)))
        if tag:
            stmt = stmt.where(Meeting.id.in_(select(MeetingTag.meeting_id).where(func.lower(MeetingTag.name) == tag.lower())))
        if date_from:
            stmt = stmt.where(Meeting.date >= date_from)
        if date_to:
            stmt = stmt.where(Meeting.date <= date_to)
        total = self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        order = Meeting.date.asc() if sort == "oldest" else Meeting.date.desc()
        stmt = stmt.options(*detail_options()).order_by(order, Meeting.id.desc()).limit(page_size).offset((page - 1) * page_size)
        return list(self.db.scalars(stmt).all()), total

    def action_item_counts(self, ids: list[int]) -> dict[int, int]:
        if not ids:
            return {}
        rows = self.db.execute(
            select(ActionItem.meeting_id, func.count()).where(ActionItem.meeting_id.in_(ids)).group_by(ActionItem.meeting_id)
        ).all()
        return {mid: c for mid, c in rows}

    def filter_options(self) -> tuple[list[str], list[str]]:
        people = self.db.scalars(select(Participant.name).distinct().order_by(Participant.name)).all()
        tags = self.db.scalars(select(MeetingTag.name).distinct().order_by(MeetingTag.name)).all()
        return list(people), list(tags)

    def add(self, meeting: Meeting) -> Meeting:
        self.db.add(meeting)
        self.db.flush()
        return meeting

    def delete(self, meeting: Meeting) -> None:
        self.db.delete(meeting)

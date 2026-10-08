"""Data access for transcript segments, including FTS5-backed search (with LIKE fallback)."""
from sqlalchemy import select, text
from sqlalchemy.orm import Session, selectinload

from app.core.fts import build_match_query, fts_available
from app.models import TranscriptSegment


def like_pattern(q: str) -> str:
    escaped = q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def matching_segment_ids(db: Session, q: str, meeting_id: int | None = None, limit: int = 200) -> list[int]:
    """Return segment ids matching `q`, best matches first. Uses FTS5 when present."""
    if not q or not q.strip():
        return []
    conn = db.connection()
    match = build_match_query(q)
    if match and fts_available(conn):
        sql = "SELECT f.rowid FROM transcript_fts f"
        params: dict = {"m": match, "limit": limit}
        if meeting_id is not None:
            sql += " JOIN transcript_segments s ON s.id = f.rowid WHERE transcript_fts MATCH :m AND s.meeting_id = :mid"
            params["mid"] = meeting_id
            sql += " ORDER BY s.start_time LIMIT :limit"
        else:
            sql += " WHERE transcript_fts MATCH :m ORDER BY rank LIMIT :limit"
        return [r[0] for r in conn.execute(text(sql), params).all()]
    stmt = select(TranscriptSegment.id).where(TranscriptSegment.text.ilike(like_pattern(q), escape="\\"))
    if meeting_id is not None:
        stmt = stmt.where(TranscriptSegment.meeting_id == meeting_id)
    return list(db.scalars(stmt.order_by(TranscriptSegment.start_time).limit(limit)).all())


class TranscriptRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_for_meeting(self, meeting_id: int) -> list[TranscriptSegment]:
        stmt = (
            select(TranscriptSegment).where(TranscriptSegment.meeting_id == meeting_id)
            .options(selectinload(TranscriptSegment.participant), selectinload(TranscriptSegment.comments),
                     selectinload(TranscriptSegment.highlights))
            .order_by(TranscriptSegment.sequence_number)
        )
        return list(self.db.scalars(stmt).all())

    def get(self, segment_id: int) -> TranscriptSegment | None:
        return self.db.get(TranscriptSegment, segment_id)

    def get_in_meeting(self, meeting_id: int, segment_id: int) -> TranscriptSegment | None:
        seg = self.db.get(TranscriptSegment, segment_id)
        return seg if seg and seg.meeting_id == meeting_id else None

    def next_sequence(self, meeting_id: int) -> int:
        last = self.db.scalar(
            select(TranscriptSegment.sequence_number).where(TranscriptSegment.meeting_id == meeting_id)
            .order_by(TranscriptSegment.sequence_number.desc()).limit(1)
        )
        return (last or 0) + 1

    def segments_by_ids(self, ids: list[int]) -> list[TranscriptSegment]:
        if not ids:
            return []
        stmt = select(TranscriptSegment).where(TranscriptSegment.id.in_(ids)).options(
            selectinload(TranscriptSegment.participant), selectinload(TranscriptSegment.meeting))
        by_id = {s.id: s for s in self.db.scalars(stmt).all()}
        return [by_id[i] for i in ids if i in by_id]

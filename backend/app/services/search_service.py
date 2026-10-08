"""Global search across titles, participants, transcripts (FTS5), summaries, action items and topics."""
from sqlalchemy import String, cast, select
from sqlalchemy.orm import Session

from app.models import ActionItem, Meeting, MeetingSummary, Participant, Topic
from app.repositories.transcript_repository import TranscriptRepository, like_pattern, matching_segment_ids
from app.schemas.search import SearchHit, SearchResults


class SearchService:
    PER_TYPE = 15

    def __init__(self, db: Session):
        self.db = db

    def search(self, q: str) -> SearchResults:
        q = q.strip()
        if len(q) < 2:
            return SearchResults(query=q, total=0, hits=[])
        pat = like_pattern(q)
        hits: list[SearchHit] = []
        n = self.PER_TYPE

        def hit(m: Meeting, type_: str, text: str, ts=None, seg=None, who=None) -> SearchHit:
            return SearchHit(type=type_, meeting_id=m.id, meeting_title=m.title, meeting_date=m.date.isoformat(),
                             text=text, timestamp=ts, segment_id=seg, participant=who)

        for m in self.db.scalars(select(Meeting).where(Meeting.title.ilike(pat, escape="\\")).order_by(Meeting.date.desc()).limit(n)):
            hits.append(hit(m, "title", m.title))
        rows = self.db.execute(select(Participant, Meeting).join(Meeting).where(Participant.name.ilike(pat, escape="\\"))
                               .order_by(Meeting.date.desc()).limit(n)).all()
        hits += [hit(m, "participant", f"{p.name}" + (f" · {p.role}" if p.role else ""), who=p.name) for p, m in rows]
        ids = matching_segment_ids(self.db, q, limit=n * 2)
        for s in TranscriptRepository(self.db).segments_by_ids(ids):
            hits.append(hit(s.meeting, "transcript", s.text, s.start_time, s.id, s.participant.name if s.participant else None))
        rows = self.db.execute(select(MeetingSummary, Meeting).join(Meeting).where(
            MeetingSummary.overview.ilike(pat, escape="\\") | cast(MeetingSummary.key_takeaways, String).ilike(pat, escape="\\")
            | cast(MeetingSummary.decisions, String).ilike(pat, escape="\\")).limit(n)).all()
        hits += [hit(m, "summary", s.overview[:240]) for s, m in rows]
        rows = self.db.execute(select(ActionItem, Meeting).join(Meeting).where(
            ActionItem.title.ilike(pat, escape="\\") | ActionItem.description.ilike(pat, escape="\\")).limit(n)).all()
        hits += [hit(m, "action_item", a.title, who=a.assignee) for a, m in rows]
        rows = self.db.execute(select(Topic, Meeting).join(Meeting).where(Topic.name.ilike(pat, escape="\\")).limit(n)).all()
        hits += [hit(m, "topic", t.name, t.start_time) for t, m in rows]
        return SearchResults(query=q, total=len(hits), hits=hits)

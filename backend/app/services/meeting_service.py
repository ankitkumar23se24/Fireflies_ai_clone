"""Meeting use-cases: list/create/update/delete, import and AI enrichment."""
from datetime import date, datetime, timezone

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import NotFoundError, PayloadTooLarge, ValidationFailed
from app.models import (ActionItem, Chapter, Meeting, MeetingSummary, MeetingTag, Participant, Topic,
                        TranscriptSegment)
from app.repositories.meeting_repository import MeetingRepository
from app.schemas.meeting import (FilterOptions, MeetingCreate, MeetingDetail, MeetingListItem, MeetingUpdate,
                                 Page, SegmentIn)
from app.services.ai_service import AIService, Seg, get_ai_service
from app.services.transcript_parser import ParsedSegment, parse_transcript

ALLOWED_EXT = (".txt", ".vtt", ".json")


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class MeetingService:
    def __init__(self, db: Session, ai: AIService | None = None):
        self.db = db
        self.repo = MeetingRepository(db)
        self.ai = ai or get_ai_service()

    # ---------- reads ----------
    def get_or_404(self, meeting_id: int, detail: bool = True) -> Meeting:
        m = self.repo.get(meeting_id, detail)
        if not m:
            raise NotFoundError(f"Meeting {meeting_id} not found")
        return m

    def get_detail(self, meeting_id: int) -> MeetingDetail:
        return MeetingDetail.model_validate(self.get_or_404(meeting_id))

    def list_meetings(self, *, q=None, participant=None, tag=None, date_from=None, date_to=None, sort="newest",
             page=1, page_size=12) -> Page:
        meetings, total = self.repo.find(q=q.strip() if q else None, participant=participant, tag=tag,
                                         date_from=date_from, date_to=date_to, sort=sort, page=page, page_size=page_size)
        counts = self.repo.action_item_counts([m.id for m in meetings])
        items = []
        for m in meetings:
            item = MeetingListItem.model_validate(m)
            item.summary_preview = (m.summary.overview[:220] if m.summary else None)
            item.action_item_count = counts.get(m.id, 0)
            items.append(item)
        return Page(items=items, total=total, page=page, page_size=page_size)

    def filter_options(self) -> FilterOptions:
        people, tags = self.repo.filter_options()
        return FilterOptions(participants=people, tags=tags)

    # ---------- writes ----------
    def create(self, payload: MeetingCreate, owner_id: int | None = 1) -> MeetingDetail:
        parsed: list[ParsedSegment] = []
        meta: dict = {}
        if payload.segments:
            parsed = self._from_segment_inputs(payload.segments)
        elif payload.transcript_text and payload.transcript_text.strip():
            parsed, meta = parse_transcript(payload.transcript_text, payload.transcript_format)
        meeting = self._build(payload, parsed, meta, owner_id)
        self.db.commit()
        return self.get_detail(meeting.id)

    async def create_from_upload(self, file: UploadFile, title: str | None, description: str | None,
                                 tags: list[str], owner_id: int | None = 1) -> MeetingDetail:
        name = (file.filename or "").lower()
        if not name.endswith(ALLOWED_EXT):
            raise ValidationFailed("Unsupported file type. Upload a .txt, .vtt or .json transcript.")
        limit = get_settings().max_upload_bytes
        raw = await file.read(limit + 1)
        if len(raw) > limit:
            raise PayloadTooLarge(f"File is too large (max {limit // 1024} KB).")
        try:
            content = raw.decode("utf-8-sig")
        except UnicodeDecodeError as e:
            raise ValidationFailed("File must be UTF-8 encoded text.") from e
        parsed, meta = parse_transcript(content, "auto", file.filename)
        base_title = title or meta.get("title") or (file.filename or "Imported meeting").rsplit(".", 1)[0].replace("_", " ").title()
        payload = MeetingCreate(
            title=base_title, description=description or meta.get("description"),
            date=_parse_dt(meta.get("date")), duration_seconds=meta.get("duration_seconds"),
            tags=tags or [str(t) for t in meta.get("tags", []) if isinstance(t, str)],
        )
        meeting = self._build(payload, parsed, meta, owner_id)
        self.db.commit()
        return self.get_detail(meeting.id)

    def update(self, meeting_id: int, payload: MeetingUpdate) -> MeetingDetail:
        m = self.get_or_404(meeting_id)
        data = payload.model_dump(exclude_unset=True)
        tags = data.pop("tags", None)
        if "title" in data and not data["title"]:
            raise ValidationFailed("Title cannot be empty")
        for key, value in data.items():
            setattr(m, key, value)
        if tags is not None:
            m.tags = [MeetingTag(name=t) for t in dict.fromkeys(t for t in tags if t)]
        self.db.commit()
        return self.get_detail(meeting_id)

    def delete(self, meeting_id: int) -> None:
        self.repo.delete(self.get_or_404(meeting_id, detail=False))
        self.db.commit()

    # ---------- AI ----------
    def regenerate_ai(self, meeting_id: int) -> MeetingDetail:
        m = self.get_or_404(meeting_id)
        if not m.segments:
            raise ValidationFailed("This meeting has no transcript to analyse.")
        self.enrich(m)
        self.db.commit()
        return self.get_detail(meeting_id)

    def enrich(self, m: Meeting, replace_action_items: bool = False) -> None:
        """(Re)generate summary, topics, chapters and (new) action items from the transcript."""
        segs = [Seg(s.id, s.participant.name if s.participant else "Speaker", s.start_time, s.end_time, s.text) for s in m.segments]
        res = self.ai.generate_summary(segs)
        if m.summary:
            m.summary.overview, m.summary.key_takeaways, m.summary.decisions = res.overview, res.key_takeaways, res.decisions
            m.summary.follow_ups, m.summary.generated_by, m.summary.generated_at = res.follow_ups, res.provider, _now()
        else:
            m.summary = MeetingSummary(overview=res.overview, key_takeaways=res.key_takeaways, decisions=res.decisions,
                                       follow_ups=res.follow_ups, generated_by=res.provider)
        m.topics = [Topic(name=t.name, start_time=t.start, end_time=t.end) for t in self.ai.extract_topics(segs)]
        m.chapters = [Chapter(title=c.name, summary=c.summary, start_time=c.start, end_time=c.end) for c in self.ai.extract_chapters(segs)]
        if replace_action_items:
            m.action_items = []
        existing = {a.title.lower() for a in m.action_items}
        for d in self.ai.extract_action_items(segs, m.date.date() if m.date else date.today()):
            if d.title.lower() not in existing:
                m.action_items.append(ActionItem(title=d.title, assignee=d.assignee, due_date=d.due_date, description=d.description))

    # ---------- internals ----------
    @staticmethod
    def _from_segment_inputs(items: list[SegmentIn]) -> list[ParsedSegment]:
        out = [ParsedSegment(i.speaker, i.start_time, i.end_time, i.text) for i in items]
        for idx, s in enumerate(out):
            if s.end_time is None:
                nxt = out[idx + 1].start_time if idx + 1 < len(out) else None
                s.end_time = nxt if nxt and nxt > s.start_time else s.start_time + 3
        return out

    def _build(self, payload: MeetingCreate, parsed: list[ParsedSegment], meta: dict, owner_id: int | None) -> Meeting:
        duration = payload.duration_seconds
        if duration is None:
            duration = int(max((s.end_time or 0 for s in parsed), default=0))
        meeting = Meeting(owner_id=owner_id, title=payload.title, description=payload.description,
                          date=payload.date or _now(), duration_seconds=duration, media_url=payload.media_url, status="COMPLETED")
        meeting.tags = [MeetingTag(name=t) for t in payload.tags]
        people: dict[str, Participant] = {}
        for p in payload.participants:
            people.setdefault(p.name.lower(), Participant(name=p.name, email=p.email, role=p.role))
        for s in parsed:
            people.setdefault(s.speaker.lower(), Participant(name=s.speaker))
        meeting.participants = list(people.values())
        meeting.segments = [
            TranscriptSegment(participant=people[s.speaker.lower()], start_time=s.start_time, end_time=s.end_time or s.start_time,
                              text=s.text, sequence_number=i + 1)
            for i, s in enumerate(parsed)
        ]
        self.repo.add(meeting)
        if parsed:
            self.enrich(meeting)
        return meeting


def _parse_dt(value) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return dt.astimezone(timezone.utc).replace(tzinfo=None) if dt.tzinfo else dt
    except ValueError:
        return None

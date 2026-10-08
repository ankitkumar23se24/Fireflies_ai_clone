from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationFailed
from app.models import Meeting, Participant, TranscriptSegment
from app.repositories.transcript_repository import TranscriptRepository, matching_segment_ids
from app.schemas.search import SearchHit
from app.schemas.transcript import (CommentOut, HighlightOut, SegmentOut, SegmentUpdate, TranscriptImport,
                                    TranscriptOut)
from app.services.meeting_service import MeetingService
from app.services.transcript_parser import ParsedSegment, parse_transcript


def to_segment_out(s: TranscriptSegment) -> SegmentOut:
    return SegmentOut(
        id=s.id, meeting_id=s.meeting_id, participant_id=s.participant_id,
        speaker=s.participant.name if s.participant else "Unknown", start_time=s.start_time, end_time=s.end_time,
        text=s.text, sequence_number=s.sequence_number,
        comments=[CommentOut.model_validate(c) for c in s.comments],
        highlights=[HighlightOut.model_validate(h) for h in s.highlights],
    )


class TranscriptService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = TranscriptRepository(db)
        self.meetings = MeetingService(db)

    def get(self, meeting_id: int) -> TranscriptOut:
        self.meetings.get_or_404(meeting_id, detail=False)
        segs = [to_segment_out(s) for s in self.repo.list_for_meeting(meeting_id)]
        return TranscriptOut(meeting_id=meeting_id, segments=segs, speakers=list(dict.fromkeys(s.speaker for s in segs)))

    def import_transcript(self, meeting_id: int, payload: TranscriptImport) -> TranscriptOut:
        meeting = self.meetings.get_or_404(meeting_id)
        if payload.segments:
            parsed = MeetingService._from_segment_inputs(payload.segments)
        else:
            parsed, _ = parse_transcript(payload.text or "", payload.format)
        if payload.mode == "replace":
            for s in list(meeting.segments):
                self.db.delete(s)
            self.db.flush()
            self.db.expire(meeting, ["segments"])
            seq, offset = 1, 0.0
        else:
            seq = self.repo.next_sequence(meeting_id)
            offset = max((s.end_time for s in meeting.segments), default=0.0)
            if parsed and parsed[0].start_time < offset:  # appended text with its own clock restarts at 0
                shift = offset
                for p in parsed:
                    p.start_time += shift
                    p.end_time = (p.end_time or p.start_time) + shift
        people = {p.name.lower(): p for p in meeting.participants}
        for p in parsed:
            if p.speaker.lower() not in people:
                person = Participant(meeting_id=meeting_id, name=p.speaker)
                self.db.add(person)
                people[p.speaker.lower()] = person
        self.db.flush()
        for i, p in enumerate(parsed):
            self.db.add(TranscriptSegment(meeting_id=meeting_id, participant_id=people[p.speaker.lower()].id,
                                          start_time=p.start_time, end_time=p.end_time or p.start_time, text=p.text, sequence_number=seq + i))
        self.db.flush()
        self.db.expire(meeting, ["segments", "participants"])
        last_end = max((s.end_time for s in meeting.segments), default=0)
        meeting.duration_seconds = max(meeting.duration_seconds, int(last_end))
        self.meetings.enrich(meeting)
        self.db.commit()
        return self.get(meeting_id)

    def update_segment(self, segment_id: int, payload: SegmentUpdate) -> SegmentOut:
        seg = self.repo.get(segment_id)
        if not seg:
            raise NotFoundError(f"Transcript segment {segment_id} not found")
        data = payload.model_dump(exclude_unset=True)
        speaker = data.pop("speaker", None)
        for k, v in data.items():
            if v is not None:
                setattr(seg, k, v)
        if seg.end_time < seg.start_time:
            raise ValidationFailed("end_time must be greater than or equal to start_time")
        if speaker:
            person = self.db.scalars(select(Participant).where(Participant.meeting_id == seg.meeting_id, Participant.name == speaker)).first()
            if not person:
                person = Participant(meeting_id=seg.meeting_id, name=speaker)
                self.db.add(person)
                self.db.flush()
            seg.participant_id = person.id
        self.db.commit()
        self.db.refresh(seg)
        return to_segment_out(self.repo.segments_by_ids([seg.id])[0])

    def delete_segment(self, segment_id: int) -> None:
        seg = self.repo.get(segment_id)
        if not seg:
            raise NotFoundError(f"Transcript segment {segment_id} not found")
        self.db.delete(seg)
        self.db.commit()

    def search(self, meeting_id: int, q: str) -> list[SearchHit]:
        meeting = self.meetings.get_or_404(meeting_id, detail=False)
        ids = matching_segment_ids(self.db, q, meeting_id=meeting_id, limit=300)
        return [
            SearchHit(type="transcript", meeting_id=meeting.id, meeting_title=meeting.title, meeting_date=meeting.date.isoformat(),
                      text=s.text, timestamp=s.start_time, segment_id=s.id, participant=s.participant.name if s.participant else None)
            for s in sorted(self.repo.segments_by_ids(ids), key=lambda x: x.start_time)
        ]

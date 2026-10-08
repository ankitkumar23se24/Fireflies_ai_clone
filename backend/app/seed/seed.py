"""Seed the database with realistic fictional meetings.

Usage:  python -m app.seed.seed [--reset]
Summaries/topics/action items are produced by the (heuristic) AI service, so the seeded data
exercises the same code path as user-created meetings.
"""
import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models import Comment, Highlight, Meeting, MeetingTag, Participant, TranscriptSegment, User
from app.services.meeting_service import MeetingService
from app.services.transcript_parser import _estimate_duration

DATA = Path(__file__).with_name("sample_data.json")
STATUS_CYCLE = ["DONE", "IN_PROGRESS", "TODO", "DONE", "TODO"]


def seed(db: Session, reset: bool = False) -> int:
    if reset:
        for table in ("comments", "highlights", "transcript_segments", "action_items", "topics", "chapters",
                      "meeting_summaries", "meeting_tags", "participants", "meetings", "users"):
            db.execute(text(f"DELETE FROM {table}"))
        db.commit()
    if db.scalar(select(User).limit(1)):
        return 0
    user = User(id=1, name="Demo User", email="demo@example.com", avatar_url=None)
    db.add(user)
    db.flush()
    service = MeetingService(db)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    meetings = json.loads(DATA.read_text())["meetings"]
    for idx, spec in enumerate(meetings):
        when = (now - timedelta(days=spec["days_ago"])).replace(hour=spec["hour"], minute=0, second=0, microsecond=0)
        duration = spec["duration_minutes"] * 60
        m = Meeting(owner_id=user.id, title=spec["title"], description=spec["description"], date=when,
                    duration_seconds=duration, media_url=None, status="COMPLETED")
        m.tags = [MeetingTag(name=t) for t in spec["tags"]]
        people = {p["name"]: Participant(name=p["name"], email=f"{p['name'].split()[0].lower()}@example.com", role=p.get("role"))
                  for p in spec["participants"]}
        m.participants = list(people.values())
        # lay out natural timings, then stretch so the transcript spans the meeting duration
        cursor, raw = 2.0, []
        for speaker, line in spec["lines"]:
            dur = _estimate_duration(line)
            raw.append((speaker, line, cursor, cursor + dur))
            cursor += dur + 1.5
        scale = (duration - 5) / cursor
        m.segments = [
            TranscriptSegment(participant=people[sp], text=tx, start_time=round(s * scale, 1), end_time=round(e * scale, 1), sequence_number=i + 1)
            for i, (sp, tx, s, e) in enumerate(raw)
        ]
        db.add(m)
        db.flush()
        service.enrich(m)
        for i, item in enumerate(m.action_items):  # vary statuses (older meetings are further along)
            item.status = STATUS_CYCLE[(i + idx) % len(STATUS_CYCLE)] if spec["days_ago"] > 2 else ("TODO" if i % 2 == 0 else "IN_PROGRESS")
            if item.due_date is None and i % 3 == 0:
                item.due_date = date.today() + timedelta(days=3 + i)
        if idx % 2 == 0 and len(m.segments) > 6:  # sample collaboration data
            seg = m.segments[5]
            db.add(Highlight(meeting_id=m.id, transcript_segment_id=seg.id, color="yellow", note="Important decision point"))
            db.add(Comment(meeting_id=m.id, transcript_segment_id=m.segments[3].id, text="Let's revisit this in the next sync.", author="Demo User"))
    db.commit()
    return len(meetings)


if __name__ == "__main__":
    with SessionLocal() as session:
        n = seed(session, reset="--reset" in sys.argv)
    print(f"Seeded {n} meetings" if n else "Database already seeded (use --reset to rebuild)")

"""Render meetings as TXT / Markdown (transcript, summary or full)."""
from sqlalchemy.orm import Session

from app.core.exceptions import ValidationFailed
from app.models import Meeting
from app.repositories.transcript_repository import TranscriptRepository
from app.services.ai_service import fmt_ts
from app.services.meeting_service import MeetingService
import re


def slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-") or "meeting"


class ExportService:
    def __init__(self, db: Session):
        self.db = db

    def export(self, meeting_id: int, fmt: str, scope: str) -> tuple[str, str, str]:
        """Returns (content, filename, media_type)."""
        if fmt not in ("txt", "markdown", "md"):
            raise ValidationFailed("format must be 'txt' or 'markdown'")
        if scope not in ("transcript", "summary", "full"):
            raise ValidationFailed("scope must be 'transcript', 'summary' or 'full'")
        m = MeetingService(self.db).get_or_404(meeting_id)
        segs = TranscriptRepository(self.db).list_for_meeting(meeting_id)
        md = fmt != "txt"
        parts = [self._header(m, md)]
        if scope in ("summary", "full"):
            parts.append(self._summary(m, md))
        if scope == "full":
            parts.append(self._topics_actions(m, md))
        if scope in ("transcript", "full"):
            parts.append(self._transcript(segs, md))
        ext = "md" if md else "txt"
        suffix = "" if scope == "full" else f"-{scope}"
        return "\n\n".join(p for p in parts if p).strip() + "\n", f"{slugify(m.title)}{suffix}.{ext}", "text/markdown" if md else "text/plain"

    @staticmethod
    def _h(text: str, md: bool, level: int = 2) -> str:
        return f"{'#' * level} {text}" if md else f"{text.upper()}\n{'-' * len(text)}"

    def _header(self, m: Meeting, md: bool) -> str:
        people = ", ".join(p.name for p in m.participants) or "—"
        lines = [self._h(m.title, md, 1) if md else f"{m.title}\n{'=' * len(m.title)}",
                 f"Date: {m.date:%Y-%m-%d %H:%M}", f"Duration: {fmt_ts(m.duration_seconds)}", f"Participants: {people}"]
        if m.tags:
            lines.append("Tags: " + ", ".join(t.name for t in m.tags))
        if m.description:
            lines.append(f"\n{m.description}")
        return "\n".join(f"- {l}" if md and i and not l.startswith("\n") else l for i, l in enumerate(lines))

    def _bullets(self, items: list[str], md: bool) -> str:
        return "\n".join(f"- {i}" for i in items) if items else "(none)"

    def _summary(self, m: Meeting, md: bool) -> str:
        s = m.summary
        if not s:
            return self._h("Summary", md) + "\n(not generated)"
        return "\n\n".join([
            self._h("Overview", md) + "\n" + s.overview,
            self._h("Key Takeaways", md) + "\n" + self._bullets(s.key_takeaways, md),
            self._h("Decisions", md) + "\n" + self._bullets(s.decisions, md),
            self._h("Questions / Follow-ups", md) + "\n" + self._bullets(s.follow_ups, md),
        ])

    def _topics_actions(self, m: Meeting, md: bool) -> str:
        topics = self._bullets([f"{t.name} ({fmt_ts(t.start_time)}–{fmt_ts(t.end_time)})" for t in m.topics], md)
        chapters = self._bullets([f"{fmt_ts(c.start_time)} {c.title}: {c.summary}" for c in m.chapters], md)
        box = {"DONE": "x", "TODO": " ", "IN_PROGRESS": "~"}
        actions = "\n".join(
            f"- [{box.get(a.status, ' ')}] {a.title}" + (f" — {a.assignee}" if a.assignee else "") + (f" (due {a.due_date})" if a.due_date else "") + f" [{a.status}]"
            for a in m.action_items) or "(none)"
        return "\n\n".join([self._h("Topics", md) + "\n" + topics, self._h("Chapters", md) + "\n" + chapters,
                            self._h("Action Items", md) + "\n" + actions])

    def _transcript(self, segs, md: bool) -> str:
        out = [self._h("Transcript", md)]
        for s in segs:
            who = s.participant.name if s.participant else "Unknown"
            out.append(f"**[{fmt_ts(s.start_time)}] {who}:** {s.text}" if md else f"[{fmt_ts(s.start_time)}] {who}: {s.text}")
        return "\n\n".join(out) if md else "\n".join(out)

from collections import defaultdict
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import ActionItem, Meeting, Participant, TranscriptSegment
from app.services.meeting_service import MeetingService


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db

    def overview(self) -> dict:
        now = _now()
        week_start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        meetings = list(self.db.scalars(select(Meeting).order_by(Meeting.date)).all())
        total_secs = sum(m.duration_seconds for m in meetings)
        status = dict(self.db.execute(select(ActionItem.status, func.count()).group_by(ActionItem.status)).all())
        weeks: dict[datetime, int] = defaultdict(int)
        for m in meetings:
            weeks[(m.date - timedelta(days=m.date.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)] += 1
        per_week = [{"week": (week_start - timedelta(weeks=i)).strftime("%b %d"), "meetings": weeks.get(week_start - timedelta(weeks=i), 0)}
                    for i in range(7, -1, -1)]
        trend = [{"date": m.date.strftime("%b %d"), "title": m.title, "minutes": round(m.duration_seconds / 60)} for m in meetings[-12:]]
        done, total_items = status.get("DONE", 0), sum(status.values())
        return {
            "total_meetings": len(meetings), "total_seconds": total_secs,
            "average_seconds": round(total_secs / len(meetings)) if meetings else 0,
            "meetings_this_week": sum(1 for m in meetings if m.date >= week_start),
            "meetings_this_month": sum(1 for m in meetings if m.date >= month_start),
            "action_items_total": total_items, "action_items_completed": done,
            "completion_rate": round(done / total_items * 100) if total_items else 0,
            "meetings_per_week": per_week, "duration_trend": trend,
            "action_item_status": [{"status": s, "count": status.get(s, 0)} for s in ("TODO", "IN_PROGRESS", "DONE")],
        }

    def for_meeting(self, meeting_id: int) -> dict:
        m = MeetingService(self.db).get_or_404(meeting_id, detail=False)
        rows = self.db.execute(
            select(Participant.name, func.sum(TranscriptSegment.end_time - TranscriptSegment.start_time),
                   func.count(TranscriptSegment.id), func.sum(func.length(TranscriptSegment.text)))
            .join(TranscriptSegment, TranscriptSegment.participant_id == Participant.id)
            .where(TranscriptSegment.meeting_id == meeting_id).group_by(Participant.name)
        ).all()
        talk_total = sum(r[1] or 0 for r in rows) or 1
        speakers = sorted(
            [{"speaker": n, "talk_seconds": round(t or 0), "share": round((t or 0) / talk_total * 100), "segments": c,
              "words": round((chars or 0) / 5.5)} for n, t, c, chars in rows], key=lambda x: -x["talk_seconds"])
        status = dict(self.db.execute(select(ActionItem.status, func.count()).where(ActionItem.meeting_id == meeting_id).group_by(ActionItem.status)).all())
        return {"meeting_id": m.id, "duration_seconds": m.duration_seconds, "speakers": speakers,
                "action_item_status": [{"status": s, "count": status.get(s, 0)} for s in ("TODO", "IN_PROGRESS", "DONE")]}

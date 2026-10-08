from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.transcript_repository import TranscriptRepository
from app.schemas.meeting import MeetingDetail
from app.schemas.search import AskRequest, AskResponse, Citation
from app.services.ai_service import Seg, get_ai_service
from app.services.meeting_service import MeetingService

router = APIRouter(tags=["ai"])


@router.post("/meetings/{meeting_id}/generate-summary", response_model=MeetingDetail)
def generate_summary(meeting_id: int, db: Session = Depends(get_db)):
    return MeetingService(db).regenerate_ai(meeting_id)


@router.post("/meetings/{meeting_id}/ask", response_model=AskResponse)
def ask(meeting_id: int, payload: AskRequest, db: Session = Depends(get_db)):
    MeetingService(db).get_or_404(meeting_id, detail=False)
    segs = [Seg(s.id, s.participant.name if s.participant else "Speaker", s.start_time, s.end_time, s.text)
            for s in TranscriptRepository(db).list_for_meeting(meeting_id)]
    result = get_ai_service().answer_question(segs, payload.question)
    return AskResponse(answer=result.answer, provider=result.provider,
                       citations=[Citation(segment_id=c.id, timestamp=c.start, speaker=c.speaker, text=c.text) for c in result.citations])

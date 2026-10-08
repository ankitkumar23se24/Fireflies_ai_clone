from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.search import SearchResults
from app.schemas.transcript import SegmentOut, SegmentUpdate, TranscriptImport, TranscriptOut
from app.services.transcript_service import TranscriptService

router = APIRouter(tags=["transcript"])


@router.get("/meetings/{meeting_id}/transcript", response_model=TranscriptOut)
def get_transcript(meeting_id: int, db: Session = Depends(get_db)):
    return TranscriptService(db).get(meeting_id)


@router.post("/meetings/{meeting_id}/transcript", response_model=TranscriptOut, status_code=status.HTTP_201_CREATED)
def import_transcript(meeting_id: int, payload: TranscriptImport, db: Session = Depends(get_db)):
    return TranscriptService(db).import_transcript(meeting_id, payload)


@router.get("/meetings/{meeting_id}/search", response_model=SearchResults)
def search_in_meeting(meeting_id: int, q: str = Query(..., min_length=1, max_length=200), db: Session = Depends(get_db)):
    hits = TranscriptService(db).search(meeting_id, q)
    return SearchResults(query=q, total=len(hits), hits=hits)


@router.patch("/transcript/{segment_id}", response_model=SegmentOut)
def update_segment(segment_id: int, payload: SegmentUpdate, db: Session = Depends(get_db)):
    return TranscriptService(db).update_segment(segment_id, payload)


@router.delete("/transcript/{segment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_segment(segment_id: int, db: Session = Depends(get_db)):
    TranscriptService(db).delete_segment(segment_id)
    return Response(status_code=204)

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.comment import CommentCreate, HighlightCreate, HighlightUpdate
from app.schemas.transcript import CommentOut, HighlightOut
from app.services.collaboration_service import CollaborationService

router = APIRouter(tags=["comments"])


@router.get("/meetings/{meeting_id}/comments", response_model=list[CommentOut])
def list_comments(meeting_id: int, db: Session = Depends(get_db)):
    return CollaborationService(db).list_comments(meeting_id)


@router.post("/meetings/{meeting_id}/comments", response_model=CommentOut, status_code=201)
def add_comment(meeting_id: int, payload: CommentCreate, db: Session = Depends(get_db)):
    return CollaborationService(db).add_comment(meeting_id, payload)


@router.delete("/comments/{comment_id}", status_code=204)
def delete_comment(comment_id: int, db: Session = Depends(get_db)):
    CollaborationService(db).delete_comment(comment_id)
    return Response(status_code=204)


@router.get("/meetings/{meeting_id}/highlights", response_model=list[HighlightOut])
def list_highlights(meeting_id: int, db: Session = Depends(get_db)):
    return CollaborationService(db).list_highlights(meeting_id)


@router.post("/meetings/{meeting_id}/highlights", response_model=HighlightOut, status_code=201)
def add_highlight(meeting_id: int, payload: HighlightCreate, db: Session = Depends(get_db)):
    return CollaborationService(db).add_highlight(meeting_id, payload)


@router.patch("/highlights/{highlight_id}", response_model=HighlightOut)
def update_highlight(highlight_id: int, payload: HighlightUpdate, db: Session = Depends(get_db)):
    return CollaborationService(db).update_highlight(highlight_id, payload)


@router.delete("/highlights/{highlight_id}", status_code=204)
def delete_highlight(highlight_id: int, db: Session = Depends(get_db)):
    CollaborationService(db).delete_highlight(highlight_id)
    return Response(status_code=204)

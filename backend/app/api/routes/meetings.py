from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.meeting import FilterOptions, MeetingCreate, MeetingDetail, MeetingUpdate, Page
from app.services.export_service import ExportService
from app.services.meeting_service import MeetingService

router = APIRouter(prefix="/meetings", tags=["meetings"])


@router.get("", response_model=Page)
def list_meetings(
    q: str | None = Query(None, max_length=200),
    participant: str | None = None,
    tag: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    sort: Literal["newest", "oldest"] = "newest",
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return MeetingService(db).list_meetings(q=q, participant=participant, tag=tag, date_from=date_from, date_to=date_to,
                                   sort=sort, page=page, page_size=page_size)


@router.get("/filters", response_model=FilterOptions)
def filter_options(db: Session = Depends(get_db)):
    return MeetingService(db).filter_options()


@router.post("", response_model=MeetingDetail, status_code=status.HTTP_201_CREATED)
def create_meeting(payload: MeetingCreate, db: Session = Depends(get_db)):
    return MeetingService(db).create(payload)


@router.post("/import", response_model=MeetingDetail, status_code=status.HTTP_201_CREATED)
async def import_meeting(
    file: UploadFile = File(...),
    title: str | None = Form(None, max_length=200),
    description: str | None = Form(None, max_length=2000),
    tags: str = Form(""),
    db: Session = Depends(get_db),
):
    tag_list = [t.strip() for t in tags.split(",") if t.strip()][:12]
    return await MeetingService(db).create_from_upload(file, title, description, tag_list)


@router.get("/{meeting_id}", response_model=MeetingDetail)
def get_meeting(meeting_id: int, db: Session = Depends(get_db)):
    return MeetingService(db).get_detail(meeting_id)


@router.patch("/{meeting_id}", response_model=MeetingDetail)
def update_meeting(meeting_id: int, payload: MeetingUpdate, db: Session = Depends(get_db)):
    return MeetingService(db).update(meeting_id, payload)


@router.delete("/{meeting_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_meeting(meeting_id: int, db: Session = Depends(get_db)):
    MeetingService(db).delete(meeting_id)
    return Response(status_code=204)


@router.get("/{meeting_id}/export")
def export_meeting(
    meeting_id: int,
    format: str = Query("markdown"),
    scope: Literal["transcript", "summary", "full"] = "full",
    db: Session = Depends(get_db),
):
    content, filename, media_type = ExportService(db).export(meeting_id, format, scope)
    return Response(content, media_type=f"{media_type}; charset=utf-8",
                    headers={"Content-Disposition": f'attachment; filename="{filename}"', "Access-Control-Expose-Headers": "Content-Disposition"})

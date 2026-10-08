from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.analytics_service import AnalyticsService

router = APIRouter(tags=["analytics"])


@router.get("/analytics/overview")
def overview(db: Session = Depends(get_db)):
    return AnalyticsService(db).overview()


@router.get("/meetings/{meeting_id}/analytics")
def meeting_analytics(meeting_id: int, db: Session = Depends(get_db)):
    return AnalyticsService(db).for_meeting(meeting_id)

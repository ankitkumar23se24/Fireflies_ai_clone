from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.search import SearchResults
from app.services.search_service import SearchService

router = APIRouter(tags=["search"])


@router.get("/search", response_model=SearchResults)
def global_search(q: str = Query("", max_length=200), db: Session = Depends(get_db)):
    return SearchService(db).search(q)

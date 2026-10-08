from fastapi import APIRouter

from app.api.routes import action_items, ai, analytics, comments, meetings, search, transcripts

api_router = APIRouter()


@api_router.get("/health", tags=["health"])
def health():
    return {"status": "ok"}


for module in (meetings, transcripts, action_items, comments, search, analytics, ai):
    api_router.include_router(module.router)

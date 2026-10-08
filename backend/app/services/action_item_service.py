from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models import ActionItem
from app.repositories.action_item_repository import ActionItemRepository
from app.schemas.action_item import ActionItemCreate, ActionItemUpdate
from app.services.meeting_service import MeetingService


class ActionItemService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ActionItemRepository(db)

    def list(self, meeting_id: int, status: str | None = None, assignee: str | None = None) -> list[ActionItem]:
        MeetingService(self.db).get_or_404(meeting_id, detail=False)
        return self.repo.list_for_meeting(meeting_id, status, assignee)

    def create(self, meeting_id: int, payload: ActionItemCreate) -> ActionItem:
        MeetingService(self.db).get_or_404(meeting_id, detail=False)
        item = self.repo.add(ActionItem(meeting_id=meeting_id, **payload.model_dump()))
        self.db.commit()
        return item

    def _get(self, item_id: int) -> ActionItem:
        item = self.repo.get(item_id)
        if not item:
            raise NotFoundError(f"Action item {item_id} not found")
        return item

    def update(self, item_id: int, payload: ActionItemUpdate) -> ActionItem:
        item = self._get(item_id)
        for k, v in payload.model_dump(exclude_unset=True).items():
            if k == "title" and not v:
                continue
            setattr(item, k, v)
        self.db.commit()
        return item

    def delete(self, item_id: int) -> None:
        self.repo.delete(self._get(item_id))
        self.db.commit()

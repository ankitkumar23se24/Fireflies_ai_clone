from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ActionItem


class ActionItemRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_for_meeting(self, meeting_id: int, status: str | None = None, assignee: str | None = None) -> list[ActionItem]:
        stmt = select(ActionItem).where(ActionItem.meeting_id == meeting_id)
        if status:
            stmt = stmt.where(ActionItem.status == status)
        if assignee:
            stmt = stmt.where(ActionItem.assignee == assignee)
        return list(self.db.scalars(stmt.order_by(ActionItem.id)).all())

    def get(self, item_id: int) -> ActionItem | None:
        return self.db.get(ActionItem, item_id)

    def add(self, item: ActionItem) -> ActionItem:
        self.db.add(item)
        self.db.flush()
        return item

    def delete(self, item: ActionItem) -> None:
        self.db.delete(item)

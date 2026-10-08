from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models._mixins import TimestampMixin, utcnow


class Meeting(TimestampMixin, Base):
    __tablename__ = "meetings"
    __table_args__ = (Index("ix_meetings_date", "date"), Index("ix_meetings_title", "title"))

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    date: Mapped[datetime] = mapped_column(DateTime)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0)
    media_url: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(20), default="COMPLETED")

    participants = relationship("Participant", back_populates="meeting", cascade="all, delete-orphan", order_by="Participant.id")
    segments = relationship("TranscriptSegment", back_populates="meeting", cascade="all, delete-orphan", order_by="TranscriptSegment.sequence_number")
    summary = relationship("MeetingSummary", back_populates="meeting", cascade="all, delete-orphan", uselist=False)
    action_items = relationship("ActionItem", back_populates="meeting", cascade="all, delete-orphan", order_by="ActionItem.id")
    topics = relationship("Topic", back_populates="meeting", cascade="all, delete-orphan", order_by="Topic.start_time")
    chapters = relationship("Chapter", back_populates="meeting", cascade="all, delete-orphan", order_by="Chapter.start_time")
    tags = relationship("MeetingTag", back_populates="meeting", cascade="all, delete-orphan", order_by="MeetingTag.id")
    comments = relationship("Comment", back_populates="meeting", cascade="all, delete-orphan")
    highlights = relationship("Highlight", back_populates="meeting", cascade="all, delete-orphan")


class MeetingSummary(Base):
    __tablename__ = "meeting_summaries"
    id: Mapped[int] = mapped_column(primary_key=True)
    meeting_id: Mapped[int] = mapped_column(ForeignKey("meetings.id", ondelete="CASCADE"), unique=True)
    overview: Mapped[str] = mapped_column(Text, default="")
    key_takeaways: Mapped[list] = mapped_column(JSON, default=list)
    decisions: Mapped[list] = mapped_column(JSON, default=list)
    follow_ups: Mapped[list] = mapped_column(JSON, default=list)
    generated_by: Mapped[str] = mapped_column(String(30), default="heuristic")
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    meeting = relationship("Meeting", back_populates="summary")


class MeetingTag(Base):
    __tablename__ = "meeting_tags"
    __table_args__ = (Index("ix_meeting_tags_name", "name"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    meeting_id: Mapped[int] = mapped_column(ForeignKey("meetings.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(50))
    meeting = relationship("Meeting", back_populates="tags")

from sqlalchemy import Float, ForeignKey, Index, Integer, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class TranscriptSegment(Base):
    __tablename__ = "transcript_segments"
    __table_args__ = (
        UniqueConstraint("meeting_id", "sequence_number", name="uq_segment_sequence"),
        Index("ix_segments_meeting_start", "meeting_id", "start_time"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    meeting_id: Mapped[int] = mapped_column(ForeignKey("meetings.id", ondelete="CASCADE"))
    participant_id: Mapped[int | None] = mapped_column(ForeignKey("participants.id", ondelete="SET NULL"), index=True)
    start_time: Mapped[float] = mapped_column(Float)
    end_time: Mapped[float] = mapped_column(Float)
    text: Mapped[str] = mapped_column(Text)
    sequence_number: Mapped[int] = mapped_column(Integer)

    meeting = relationship("Meeting", back_populates="segments")
    participant = relationship("Participant", back_populates="segments")
    comments = relationship("Comment", back_populates="segment", cascade="all, delete-orphan", order_by="Comment.id")
    highlights = relationship("Highlight", back_populates="segment", cascade="all, delete-orphan", order_by="Highlight.id")

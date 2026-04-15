from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class DailyChallenge(Base):
    __tablename__ = "daily_challenges"
    __table_args__ = (UniqueConstraint("challenge_date", "word_length", name="uq_daily_challenges_date_length"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    challenge_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    word_length: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    word_id: Mapped[int] = mapped_column(ForeignKey("words.id", ondelete="RESTRICT"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    word = relationship("Word", back_populates="daily_challenges")

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Index, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.daily_challenge import DailyChallenge
    from app.models.game import Game


class Word(Base):
    __tablename__ = "words"
    __table_args__ = (
        UniqueConstraint("value", "language", name="uq_words_value_language"),
        Index("ix_words_length_language_active", "length", "language", "is_active"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    value: Mapped[str] = mapped_column(String(32), nullable=False)
    length: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    language: Mapped[str] = mapped_column(String(8), default="en", server_default="en", nullable=False)
    difficulty: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    games: Mapped[list["Game"]] = relationship(back_populates="word")
    daily_challenges: Mapped[list["DailyChallenge"]] = relationship(back_populates="word")

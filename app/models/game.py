from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, Enum as SAEnum, ForeignKey, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.utils.enums import GameMode, GameStatus

if TYPE_CHECKING:
    from app.models.guess import Guess
    from app.models.profile import Profile
    from app.models.word import Word


def _enum_values(enum_cls: type[GameStatus] | type[GameMode]) -> list[str]:
    return [item.value for item in enum_cls]


class Game(Base):
    __tablename__ = "games"
    __table_args__ = (
        Index("ix_games_user_status", "user_id", "status"),
        Index("ix_games_user_mode_length", "user_id", "mode", "word_length"),
        Index("ix_games_leaderboard", "status", "word_length", "score"),
        Index("ix_games_daily", "mode", "challenge_date", "word_length"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    word_id: Mapped[int] = mapped_column(ForeignKey("words.id", ondelete="RESTRICT"), nullable=False)
    word_length: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[GameStatus] = mapped_column(
        SAEnum(GameStatus, values_callable=_enum_values, native_enum=False, length=16),
        default=GameStatus.ACTIVE,
        nullable=False,
    )
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False)
    attempts_used: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    score: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    mode: Mapped[GameMode] = mapped_column(
        SAEnum(GameMode, values_callable=_enum_values, native_enum=False, length=16),
        default=GameMode.CLASSIC,
        nullable=False,
    )
    challenge_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    profile: Mapped["Profile"] = relationship(back_populates="games")
    word: Mapped["Word"] = relationship(back_populates="games")
    guesses: Mapped[list["Guess"]] = relationship(
        back_populates="game",
        cascade="all, delete-orphan",
        order_by="Guess.attempt_number",
    )

    @property
    def attempts_remaining(self) -> int:
        return max(self.max_attempts - self.attempts_used, 0)

from __future__ import annotations

from datetime import datetime
from typing import Any
import uuid

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Guess(Base):
    __tablename__ = "guesses"
    __table_args__ = (UniqueConstraint("game_id", "attempt_number", name="uq_guesses_game_attempt"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    game_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("games.id", ondelete="CASCADE"), nullable=False, index=True)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    guess_value: Mapped[str] = mapped_column(String(32), nullable=False)
    result_json: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    game = relationship("Game", back_populates="guesses")

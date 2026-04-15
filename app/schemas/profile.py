from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class StatsSummary(BaseModel):
    total_games: int = 0
    wins: int = 0
    losses: int = 0
    win_rate: float = 0.0
    current_streak: int = 0
    best_streak: int = 0
    average_attempts_on_wins: float | None = None
    total_score: int = 0


class ProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: str | None = None
    created_at: datetime
    updated_at: datetime
    last_seen_at: datetime | None = None
    stats: StatsSummary | None = None


class UpdateUsernameRequest(BaseModel):
    username: str = Field(min_length=3, max_length=32)

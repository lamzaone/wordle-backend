from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel


class LeaderboardEntry(BaseModel):
    rank: int
    user_id: UUID
    username: str | None = None
    total_score: int
    wins: int
    total_games: int
    average_attempts_on_wins: float | None = None


class DailyLeaderboardEntry(BaseModel):
    rank: int
    user_id: UUID
    username: str | None = None
    score: int
    attempts_used: int
    finished_at: datetime | None = None
    challenge_date: date
    word_length: int

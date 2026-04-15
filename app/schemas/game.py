from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.utils.enums import GameMode, GameStatus, GuessLetterStatus
from app.utils.wordle import normalize_word


class GameStartRequest(BaseModel):
    word_length: int = Field(ge=1, le=32)
    mode: GameMode = GameMode.CLASSIC


class GuessRequest(BaseModel):
    guess: str = Field(min_length=1, max_length=32)

    @field_validator("guess")
    @classmethod
    def normalize_guess(cls, value: str) -> str:
        return normalize_word(value)


class GuessLetter(BaseModel):
    letter: str
    status: GuessLetterStatus


class GuessOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    attempt_number: int
    guess_value: str
    result_json: list[GuessLetter]
    created_at: datetime


class GameOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    word_length: int
    status: GameStatus
    max_attempts: int
    attempts_used: int
    attempts_remaining: int
    started_at: datetime
    finished_at: datetime | None = None
    score: int
    mode: GameMode
    challenge_date: date | None = None
    guesses: list[GuessOut] = []


class GuessResponse(BaseModel):
    result: list[GuessLetter]
    game: GameOut
    is_correct: bool
    attempts_remaining: int


class DailyChallengeOut(BaseModel):
    challenge_date: date
    word_length: int
    mode: GameMode = GameMode.DAILY
    available: bool = True


class DailyGenerateRequest(BaseModel):
    challenge_date: date | None = None
    word_length: int = Field(ge=1, le=32)

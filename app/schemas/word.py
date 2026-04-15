from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class WordCreate(BaseModel):
    value: str = Field(min_length=1, max_length=32)
    language: str = Field(default="en", min_length=2, max_length=8)
    difficulty: int | None = Field(default=None, ge=1, le=10)
    is_active: bool = True


class WordBulkImport(BaseModel):
    words: list[str] = Field(min_length=1, max_length=5000)
    language: str = Field(default="en", min_length=2, max_length=8)
    difficulty: int | None = Field(default=None, ge=1, le=10)
    is_active: bool = True


class WordUpdateActive(BaseModel):
    is_active: bool


class WordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    value: str
    length: int
    language: str
    difficulty: int | None = None
    is_active: bool
    created_at: datetime

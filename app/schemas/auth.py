from uuid import UUID
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class AuthenticatedUserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr | None = None


class PasswordAuthRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=256)


class SupabaseUserOut(BaseModel):
    id: UUID | None = None
    email: EmailStr | None = None


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: str | None = None
    expires_in: int | None = None
    expires_at: int | None = None
    user: dict[str, Any] | None = None


class RegisterResponse(BaseModel):
    access_token: str | None = None
    token_type: str = "bearer"
    refresh_token: str | None = None
    expires_in: int | None = None
    expires_at: int | None = None
    user: dict[str, Any] | None = None
    message: str

from __future__ import annotations

import re
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import AuthenticatedUser
from app.models.profile import Profile
from app.services.errors import ConflictError, ValidationServiceError

USERNAME_PATTERN = re.compile(r"^[a-z0-9_]{3,32}$")


class AuthService:
    @staticmethod
    async def get_or_create_profile(db: AsyncSession, auth_user: AuthenticatedUser) -> Profile:
        profile = await db.get(Profile, auth_user.id)
        if profile is None:
            profile = Profile(id=auth_user.id)
            db.add(profile)
            await db.flush()
        profile.last_seen_at = datetime.now(UTC)
        return profile

    @staticmethod
    def normalize_username(username: str) -> str:
        normalized = username.strip().lower()
        if not USERNAME_PATTERN.fullmatch(normalized):
            raise ValidationServiceError("Username must be 3-32 characters using lowercase letters, numbers, or underscores.")
        return normalized

    @staticmethod
    async def update_username(db: AsyncSession, profile: Profile, username: str) -> Profile:
        normalized = AuthService.normalize_username(username)
        existing = await db.scalar(select(Profile).where(Profile.username == normalized, Profile.id != profile.id))
        if existing is not None:
            raise ConflictError("Username is already taken.")
        profile.username = normalized
        await db.commit()
        await db.refresh(profile)
        return profile

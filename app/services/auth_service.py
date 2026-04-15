from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
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

    @staticmethod
    async def supabase_password_login(settings: Settings, *, email: str, password: str) -> dict[str, Any]:
        return await AuthService._supabase_auth_request(
            settings,
            path="/auth/v1/token?grant_type=password",
            payload={"email": email, "password": password},
            error_prefix="Invalid email or password.",
        )

    @staticmethod
    async def supabase_password_register(settings: Settings, *, email: str, password: str) -> dict[str, Any]:
        return await AuthService._supabase_auth_request(
            settings,
            path="/auth/v1/signup",
            payload={"email": email, "password": password},
            error_prefix="Unable to register user.",
        )

    @staticmethod
    async def _supabase_auth_request(
        settings: Settings,
        *,
        path: str,
        payload: dict[str, str],
        error_prefix: str,
    ) -> dict[str, Any]:
        url = f"{settings.supabase_url.rstrip('/')}{path}"
        headers = {
            "apikey": settings.supabase_anon_key.get_secret_value(),
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(url, headers=headers, json=payload)

        if response.is_success:
            return response.json()

        detail = error_prefix
        try:
            body = response.json()
            detail = body.get("msg") or body.get("message") or body.get("error_description") or detail
        except ValueError:
            pass
        raise ValidationServiceError(detail)

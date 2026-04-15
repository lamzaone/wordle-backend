from __future__ import annotations

import time
from collections import defaultdict, deque
from collections.abc import AsyncGenerator

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.security import AuthenticatedUser, AuthenticationError, get_jwt_verifier
from app.db.session import get_db_session
from app.models.profile import Profile
from app.services.auth_service import AuthService
from app.services.errors import RateLimitError

def _swagger_token_url() -> str:
    prefix = get_settings().api_v1_prefix.rstrip("/")
    return f"{prefix}/auth/token" if prefix else "/auth/token"


oauth2_scheme = OAuth2PasswordBearer(tokenUrl=_swagger_token_url(), auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_db_session():
        yield session


async def get_current_auth_user(
    token: str | None = Depends(oauth2_scheme),
) -> AuthenticatedUser:
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        return await get_jwt_verifier().verify(token)
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


async def get_current_profile(
    auth_user: AuthenticatedUser = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db),
) -> Profile:
    profile = await AuthService.get_or_create_profile(db, auth_user)
    await db.commit()
    await db.refresh(profile)
    return profile


async def require_admin_profile(
    profile: Profile = Depends(get_current_profile),
    settings: Settings = Depends(get_settings),
) -> Profile:
    if profile.id not in settings.admin_user_ids:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required.")
    return profile


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._events: dict[str, deque[float]] = defaultdict(deque)

    def check(self, *, key: str, limit: int, window_seconds: int = 60) -> None:
        if limit <= 0:
            return
        now = time.monotonic()
        events = self._events[key]
        while events and now - events[0] > window_seconds:
            events.popleft()
        if len(events) >= limit:
            raise RateLimitError("Too many guesses. Please wait before trying again.")
        events.append(now)


_guess_rate_limiter = InMemoryRateLimiter()


async def limit_guess_rate(
    request: Request,
    profile: Profile = Depends(get_current_profile),
    settings: Settings = Depends(get_settings),
) -> None:
    client_host = request.client.host if request.client else "unknown"
    _guess_rate_limiter.check(
        key=f"{profile.id}:{client_host}",
        limit=settings.guesses_rate_limit_per_minute,
    )

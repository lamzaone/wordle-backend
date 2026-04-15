from __future__ import annotations

from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import Settings, get_settings
from app.models.daily_challenge import DailyChallenge
from app.services.errors import NotFoundError
from app.services.word_service import WordService


class DailyChallengeService:
    @staticmethod
    def current_challenge_date(settings: Settings | None = None) -> date:
        active_settings = settings or get_settings()
        try:
            tz = ZoneInfo(active_settings.daily_challenge_timezone)
        except ZoneInfoNotFoundError:
            tz = UTC
        return datetime.now(tz).date()

    @staticmethod
    async def get_challenge(
        db: AsyncSession,
        *,
        challenge_date: date,
        word_length: int,
    ) -> DailyChallenge | None:
        return await db.scalar(
            select(DailyChallenge)
            .options(selectinload(DailyChallenge.word))
            .where(
                DailyChallenge.challenge_date == challenge_date,
                DailyChallenge.word_length == word_length,
            )
        )

    @staticmethod
    async def get_or_create_challenge(
        db: AsyncSession,
        *,
        challenge_date: date,
        word_length: int,
        settings: Settings | None = None,
    ) -> DailyChallenge:
        active_settings = settings or get_settings()
        WordService.ensure_allowed_length(word_length, settings=active_settings)
        existing = await DailyChallengeService.get_challenge(
            db,
            challenge_date=challenge_date,
            word_length=word_length,
        )
        if existing is not None:
            return existing

        word = await WordService.get_random_active_word(
            db,
            word_length=word_length,
            settings=active_settings,
        )
        challenge = DailyChallenge(
            challenge_date=challenge_date,
            word_length=word_length,
            word_id=word.id,
        )
        db.add(challenge)
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            existing = await DailyChallengeService.get_challenge(
                db,
                challenge_date=challenge_date,
                word_length=word_length,
            )
            if existing is None:
                raise
            return existing
        await db.refresh(challenge)
        return challenge

    @staticmethod
    async def require_challenge(
        db: AsyncSession,
        *,
        challenge_date: date,
        word_length: int,
    ) -> DailyChallenge:
        challenge = await DailyChallengeService.get_challenge(
            db,
            challenge_date=challenge_date,
            word_length=word_length,
        )
        if challenge is None:
            raise NotFoundError("Daily challenge is not available for that date and word length.")
        return challenge

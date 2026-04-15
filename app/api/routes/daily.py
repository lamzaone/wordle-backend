from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.deps import get_db, require_admin_profile
from app.schemas.game import DailyChallengeOut, DailyGenerateRequest
from app.services.daily_service import DailyChallengeService

router = APIRouter(prefix="/daily", tags=["daily"])


@router.get("/today", response_model=DailyChallengeOut)
async def today(
    word_length: int = Query(5, ge=1, le=32),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> DailyChallengeOut:
    challenge_date = DailyChallengeService.current_challenge_date(settings)
    challenge = await DailyChallengeService.get_or_create_challenge(
        db,
        challenge_date=challenge_date,
        word_length=word_length,
        settings=settings,
    )
    return DailyChallengeOut(challenge_date=challenge.challenge_date, word_length=challenge.word_length)


@router.post("/generate", response_model=DailyChallengeOut, dependencies=[Depends(require_admin_profile)])
async def generate_daily(
    payload: DailyGenerateRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> DailyChallengeOut:
    challenge = await DailyChallengeService.get_or_create_challenge(
        db,
        challenge_date=payload.challenge_date or DailyChallengeService.current_challenge_date(settings),
        word_length=payload.word_length,
        settings=settings,
    )
    return DailyChallengeOut(challenge_date=challenge.challenge_date, word_length=challenge.word_length)

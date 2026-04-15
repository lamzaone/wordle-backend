from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.schemas.common import PaginatedResponse
from app.schemas.leaderboard import DailyLeaderboardEntry, LeaderboardEntry
from app.services.leaderboard_service import LeaderboardService
from app.utils.pagination import Pagination, pagination_params

router = APIRouter(prefix="/leaderboards", tags=["leaderboards"])


@router.get("/global", response_model=PaginatedResponse[LeaderboardEntry])
async def global_leaderboard(
    pagination: Pagination = Depends(pagination_params),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[LeaderboardEntry]:
    entries = await LeaderboardService.global_leaderboard(
        db,
        limit=pagination.limit,
        offset=pagination.offset,
    )
    return PaginatedResponse(items=entries, limit=pagination.limit, offset=pagination.offset)


@router.get("/by-length/{word_length}", response_model=PaginatedResponse[LeaderboardEntry])
async def by_length_leaderboard(
    word_length: int,
    pagination: Pagination = Depends(pagination_params),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[LeaderboardEntry]:
    entries = await LeaderboardService.by_length_leaderboard(
        db,
        word_length=word_length,
        limit=pagination.limit,
        offset=pagination.offset,
    )
    return PaginatedResponse(items=entries, limit=pagination.limit, offset=pagination.offset)


@router.get("/daily", response_model=PaginatedResponse[DailyLeaderboardEntry])
async def daily_leaderboard(
    challenge_date: date = Query(alias="date"),
    word_length: int = Query(5, ge=1, le=32),
    pagination: Pagination = Depends(pagination_params),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[DailyLeaderboardEntry]:
    entries = await LeaderboardService.daily_leaderboard(
        db,
        challenge_date=challenge_date,
        word_length=word_length,
        limit=pagination.limit,
        offset=pagination.offset,
    )
    return PaginatedResponse(items=entries, limit=pagination.limit, offset=pagination.offset)

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_profile, get_db
from app.models.profile import Profile
from app.schemas.profile import ProfileOut, UpdateUsernameRequest
from app.services.auth_service import AuthService
from app.services.stats_service import StatsService

router = APIRouter(tags=["profile"])


@router.get("/me", response_model=ProfileOut)
async def me(
    profile: Profile = Depends(get_current_profile),
    db: AsyncSession = Depends(get_db),
) -> ProfileOut:
    stats = await StatsService.get_user_stats(db, user_id=profile.id)
    response = ProfileOut.model_validate(profile)
    response.stats = stats
    return response


@router.patch("/me/username", response_model=ProfileOut)
async def update_username(
    payload: UpdateUsernameRequest,
    profile: Profile = Depends(get_current_profile),
    db: AsyncSession = Depends(get_db),
) -> ProfileOut:
    updated = await AuthService.update_username(db, profile, payload.username)
    stats = await StatsService.get_user_stats(db, user_id=updated.id)
    response = ProfileOut.model_validate(updated)
    response.stats = stats
    return response

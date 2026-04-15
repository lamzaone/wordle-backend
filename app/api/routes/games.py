from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.deps import get_current_profile, get_db, limit_guess_rate
from app.models.profile import Profile
from app.schemas.common import PaginatedResponse
from app.schemas.game import GameOut, GameStartRequest, GuessRequest, GuessResponse
from app.services.game_service import GameService
from app.utils.enums import GameMode, GameStatus
from app.utils.pagination import Pagination, pagination_params

router = APIRouter(prefix="/games", tags=["games"])


@router.post("/start", response_model=GameOut, status_code=201)
async def start_game(
    payload: GameStartRequest,
    profile: Profile = Depends(get_current_profile),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> GameOut:
    game = await GameService.start_game(
        db,
        profile=profile,
        word_length=payload.word_length,
        mode=payload.mode,
        settings=settings,
    )
    return GameOut.model_validate(game)


@router.get("/{game_id}", response_model=GameOut)
async def get_game(
    game_id: UUID,
    profile: Profile = Depends(get_current_profile),
    db: AsyncSession = Depends(get_db),
) -> GameOut:
    game = await GameService.get_game_for_user(db, profile=profile, game_id=game_id)
    return GameOut.model_validate(game)


@router.get("", response_model=PaginatedResponse[GameOut])
async def list_games(
    pagination: Pagination = Depends(pagination_params),
    status: GameStatus | None = Query(default=None),
    mode: GameMode | None = Query(default=None),
    profile: Profile = Depends(get_current_profile),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[GameOut]:
    games = await GameService.list_games(
        db,
        profile=profile,
        limit=pagination.limit,
        offset=pagination.offset,
        status=status,
        mode=mode,
    )
    return PaginatedResponse(
        items=[GameOut.model_validate(game) for game in games],
        limit=pagination.limit,
        offset=pagination.offset,
    )


@router.post("/{game_id}/guess", response_model=GuessResponse)
async def submit_guess(
    game_id: UUID,
    payload: GuessRequest,
    _: None = Depends(limit_guess_rate),
    profile: Profile = Depends(get_current_profile),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> GuessResponse:
    submission = await GameService.submit_guess(
        db,
        profile=profile,
        game_id=game_id,
        guess=payload.guess,
        settings=settings,
    )
    return GuessResponse(
        result=submission.result,
        game=GameOut.model_validate(submission.game),
        is_correct=submission.is_correct,
        attempts_remaining=submission.attempts_remaining,
    )


@router.post("/{game_id}/abandon", response_model=GameOut)
async def abandon_game(
    game_id: UUID,
    profile: Profile = Depends(get_current_profile),
    db: AsyncSession = Depends(get_db),
) -> GameOut:
    game = await GameService.abandon_game(db, profile=profile, game_id=game_id)
    return GameOut.model_validate(game)

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.deps import get_db, require_admin_profile
from app.schemas.common import PaginatedResponse
from app.schemas.word import WordBulkImport, WordCreate, WordOut, WordUpdateActive
from app.services.word_service import WordService
from app.utils.pagination import Pagination, pagination_params

router = APIRouter(prefix="/admin/words", tags=["admin-words"], dependencies=[Depends(require_admin_profile)])


@router.post("", response_model=WordOut, status_code=201)
async def add_word(
    payload: WordCreate,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> WordOut:
    word = await WordService.add_word(
        db,
        value=payload.value,
        language=payload.language,
        difficulty=payload.difficulty,
        is_active=payload.is_active,
        settings=settings,
    )
    return WordOut.model_validate(word)


@router.post("/bulk", response_model=list[WordOut], status_code=201)
async def bulk_import_words(
    payload: WordBulkImport,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> list[WordOut]:
    words = await WordService.bulk_import(
        db,
        words=payload.words,
        language=payload.language,
        difficulty=payload.difficulty,
        is_active=payload.is_active,
        settings=settings,
    )
    return [WordOut.model_validate(word) for word in words]


@router.patch("/{word_id}/active", response_model=WordOut)
async def set_word_active(
    word_id: int,
    payload: WordUpdateActive,
    db: AsyncSession = Depends(get_db),
) -> WordOut:
    word = await WordService.set_active(db, word_id=word_id, is_active=payload.is_active)
    return WordOut.model_validate(word)


@router.get("", response_model=PaginatedResponse[WordOut])
async def list_words(
    pagination: Pagination = Depends(pagination_params),
    word_length: int | None = Query(default=None, ge=1, le=32),
    language: str | None = Query(default=None, min_length=2, max_length=8),
    is_active: bool | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[WordOut]:
    words = await WordService.list_words(
        db,
        limit=pagination.limit,
        offset=pagination.offset,
        word_length=word_length,
        language=language,
        is_active=is_active,
    )
    return PaginatedResponse(
        items=[WordOut.model_validate(word) for word in words],
        limit=pagination.limit,
        offset=pagination.offset,
    )

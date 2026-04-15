from __future__ import annotations

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.models.word import Word
from app.services.errors import ConflictError, NotFoundError, ValidationServiceError
from app.utils.wordle import WordValidationError, validate_word_value


class WordService:
    @staticmethod
    def ensure_allowed_length(word_length: int, settings: Settings | None = None) -> None:
        active_settings = settings or get_settings()
        if word_length not in active_settings.allowed_word_lengths:
            allowed = ", ".join(str(length) for length in active_settings.allowed_word_lengths)
            raise ValidationServiceError(f"Word length must be one of: {allowed}.")

    @staticmethod
    def normalize_for_insert(value: str, settings: Settings | None = None) -> str:
        try:
            return validate_word_value(value, allowed_lengths=(settings or get_settings()).allowed_word_lengths)
        except WordValidationError as exc:
            raise ValidationServiceError(str(exc)) from exc

    @staticmethod
    async def add_word(
        db: AsyncSession,
        *,
        value: str,
        language: str = "en",
        difficulty: int | None = None,
        is_active: bool = True,
        settings: Settings | None = None,
    ) -> Word:
        normalized = WordService.normalize_for_insert(value, settings=settings)
        language = language.strip().lower()
        existing = await db.scalar(select(Word).where(Word.value == normalized, Word.language == language))
        if existing is not None:
            raise ConflictError("Word already exists for this language.")

        word = Word(
            value=normalized,
            length=len(normalized),
            language=language,
            difficulty=difficulty,
            is_active=is_active,
        )
        db.add(word)
        await db.commit()
        await db.refresh(word)
        return word

    @staticmethod
    async def bulk_import(
        db: AsyncSession,
        *,
        words: list[str],
        language: str = "en",
        difficulty: int | None = None,
        is_active: bool = True,
        settings: Settings | None = None,
    ) -> list[Word]:
        active_settings = settings or get_settings()
        normalized_words = sorted({WordService.normalize_for_insert(word, settings=active_settings) for word in words})
        language = language.strip().lower()
        existing_values = set(
            (
                await db.execute(
                    select(Word.value).where(Word.language == language, Word.value.in_(normalized_words))
                )
            ).scalars()
        )
        created = [
            Word(
                value=value,
                length=len(value),
                language=language,
                difficulty=difficulty,
                is_active=is_active,
            )
            for value in normalized_words
            if value not in existing_values
        ]
        db.add_all(created)
        await db.commit()
        for word in created:
            await db.refresh(word)
        return created

    @staticmethod
    async def set_active(db: AsyncSession, *, word_id: int, is_active: bool) -> Word:
        word = await db.get(Word, word_id)
        if word is None:
            raise NotFoundError("Word not found.")
        word.is_active = is_active
        await db.commit()
        await db.refresh(word)
        return word

    @staticmethod
    async def list_words(
        db: AsyncSession,
        *,
        limit: int,
        offset: int,
        word_length: int | None = None,
        language: str | None = None,
        is_active: bool | None = None,
    ) -> list[Word]:
        stmt: Select[tuple[Word]] = select(Word).order_by(Word.length.asc(), Word.value.asc()).limit(limit).offset(offset)
        if word_length is not None:
            stmt = stmt.where(Word.length == word_length)
        if language is not None:
            stmt = stmt.where(Word.language == language.strip().lower())
        if is_active is not None:
            stmt = stmt.where(Word.is_active.is_(is_active))
        return list((await db.execute(stmt)).scalars())

    @staticmethod
    async def get_random_active_word(
        db: AsyncSession,
        *,
        word_length: int,
        language: str = "en",
        settings: Settings | None = None,
    ) -> Word:
        WordService.ensure_allowed_length(word_length, settings=settings)
        word = await db.scalar(
            select(Word)
            .where(Word.length == word_length, Word.language == language, Word.is_active.is_(True))
            .order_by(func.random())
            .limit(1)
        )
        if word is None:
            raise NotFoundError(f"No active {word_length}-letter words are available.")
        return word

    @staticmethod
    async def active_word_exists(
        db: AsyncSession,
        *,
        value: str,
        word_length: int,
        language: str = "en",
    ) -> bool:
        normalized = validate_word_value(value, expected_length=word_length)
        exists_query = select(Word.id).where(
            Word.value == normalized,
            Word.length == word_length,
            Word.language == language,
            Word.is_active.is_(True),
        )
        return (await db.scalar(exists_query)) is not None

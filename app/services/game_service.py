from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import Settings, get_settings
from app.models.game import Game
from app.models.guess import Guess
from app.models.profile import Profile
from app.models.word import Word
from app.services.daily_service import DailyChallengeService
from app.services.errors import ConflictError, NotFoundError, ValidationServiceError
from app.services.scoring_service import calculate_score
from app.services.word_service import WordService
from app.utils.enums import GameMode, GameStatus
from app.utils.wordle import WordValidationError, evaluate_guess, validate_word_value


@dataclass(frozen=True)
class GuessResolution:
    result: list[dict[str, str]]
    status: GameStatus
    attempts_used: int
    score: int
    finished_at: datetime | None
    is_correct: bool


@dataclass(frozen=True)
class GuessSubmission:
    game: Game
    result: list[dict[str, str]]
    is_correct: bool
    attempts_remaining: int


def resolve_guess_state(
    *,
    target_word: str,
    guess: str,
    word_length: int,
    current_attempts: int,
    max_attempts: int,
    mode: GameMode,
    settings: Settings | None = None,
) -> GuessResolution:
    try:
        normalized_guess = validate_word_value(guess, expected_length=word_length)
    except WordValidationError as exc:
        raise ValidationServiceError(str(exc)) from exc

    result = evaluate_guess(target_word, normalized_guess)
    attempts_used = current_attempts + 1
    is_correct = normalized_guess == target_word
    finished_at: datetime | None = None
    status = GameStatus.ACTIVE
    score = 0

    if is_correct:
        status = GameStatus.WON
        finished_at = datetime.now(UTC)
        score = calculate_score(
            word_length=word_length,
            max_attempts=max_attempts,
            attempts_used=attempts_used,
            won=True,
            mode=mode,
            settings=settings,
        )
    elif attempts_used >= max_attempts:
        status = GameStatus.LOST
        finished_at = datetime.now(UTC)

    return GuessResolution(
        result=result,
        status=status,
        attempts_used=attempts_used,
        score=score,
        finished_at=finished_at,
        is_correct=is_correct,
    )


class GameService:
    @staticmethod
    def _base_game_query() -> Select[tuple[Game]]:
        return select(Game).options(selectinload(Game.guesses), selectinload(Game.word))

    @staticmethod
    async def start_game(
        db: AsyncSession,
        *,
        profile: Profile,
        word_length: int,
        mode: GameMode,
        settings: Settings | None = None,
    ) -> Game:
        active_settings = settings or get_settings()
        WordService.ensure_allowed_length(word_length, settings=active_settings)

        challenge_date: date | None = None
        if mode == GameMode.DAILY:
            challenge_date = DailyChallengeService.current_challenge_date(active_settings)
            existing_daily = await db.scalar(
                GameService._base_game_query()
                .where(
                    Game.user_id == profile.id,
                    Game.mode == GameMode.DAILY,
                    Game.challenge_date == challenge_date,
                    Game.word_length == word_length,
                )
                .order_by(Game.created_at.desc())
                .limit(1)
            )
            if existing_daily is not None:
                return existing_daily
            challenge = await DailyChallengeService.get_or_create_challenge(
                db,
                challenge_date=challenge_date,
                word_length=word_length,
                settings=active_settings,
            )
            word_id = challenge.word_id
        else:
            if active_settings.one_active_classic_game_per_length:
                existing_active = await db.scalar(
                    GameService._base_game_query()
                    .where(
                        Game.user_id == profile.id,
                        Game.mode == GameMode.CLASSIC,
                        Game.status == GameStatus.ACTIVE,
                        Game.word_length == word_length,
                    )
                    .order_by(Game.created_at.desc())
                    .limit(1)
                )
                if existing_active is not None:
                    return existing_active
            word = await WordService.get_random_active_word(
                db,
                word_length=word_length,
                settings=active_settings,
            )
            word_id = word.id

        game = Game(
            user_id=profile.id,
            word_id=word_id,
            word_length=word_length,
            status=GameStatus.ACTIVE,
            max_attempts=active_settings.default_max_attempts,
            mode=mode,
            challenge_date=challenge_date,
        )
        db.add(game)
        await db.commit()
        return await GameService.get_game_for_user(db, profile=profile, game_id=game.id)

    @staticmethod
    async def get_game_for_user(db: AsyncSession, *, profile: Profile, game_id: UUID) -> Game:
        game = await db.scalar(
            GameService._base_game_query().where(Game.id == game_id, Game.user_id == profile.id)
        )
        if game is None:
            raise NotFoundError("Game not found.")
        return game

    @staticmethod
    async def list_games(
        db: AsyncSession,
        *,
        profile: Profile,
        limit: int,
        offset: int,
        status: GameStatus | None = None,
        mode: GameMode | None = None,
    ) -> list[Game]:
        stmt = (
            GameService._base_game_query()
            .where(Game.user_id == profile.id)
            .order_by(Game.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        if status is not None:
            stmt = stmt.where(Game.status == status)
        if mode is not None:
            stmt = stmt.where(Game.mode == mode)
        return list((await db.execute(stmt)).scalars())

    @staticmethod
    async def submit_guess(
        db: AsyncSession,
        *,
        profile: Profile,
        game_id: UUID,
        guess: str,
        settings: Settings | None = None,
    ) -> GuessSubmission:
        active_settings = settings or get_settings()
        game = await db.scalar(
            GameService._base_game_query()
            .where(Game.id == game_id, Game.user_id == profile.id)
            .with_for_update()
        )
        if game is None:
            raise NotFoundError("Game not found.")
        if game.status != GameStatus.ACTIVE:
            raise ConflictError("Game is already finished.")
        if game.word is None:
            raise NotFoundError("Game target word is unavailable.")

        try:
            normalized_guess = validate_word_value(guess, expected_length=game.word_length)
        except WordValidationError as exc:
            raise ValidationServiceError(str(exc)) from exc

        if active_settings.enforce_dictionary_guesses:
            is_known_word = await WordService.active_word_exists(
                db,
                value=normalized_guess,
                word_length=game.word_length,
            )
            if not is_known_word:
                raise ValidationServiceError("Guess is not in the active dictionary.")

        resolution = resolve_guess_state(
            target_word=game.word.value,
            guess=normalized_guess,
            word_length=game.word_length,
            current_attempts=game.attempts_used,
            max_attempts=game.max_attempts,
            mode=game.mode,
            settings=active_settings,
        )

        guess_row = Guess(
            game_id=game.id,
            attempt_number=resolution.attempts_used,
            guess_value=normalized_guess,
            result_json=resolution.result,
        )
        db.add(guess_row)
        game.attempts_used = resolution.attempts_used
        game.status = resolution.status
        game.finished_at = resolution.finished_at
        game.score = resolution.score

        await db.commit()
        refreshed_game = await GameService.get_game_for_user(db, profile=profile, game_id=game.id)
        return GuessSubmission(
            game=refreshed_game,
            result=resolution.result,
            is_correct=resolution.is_correct,
            attempts_remaining=refreshed_game.attempts_remaining,
        )

    @staticmethod
    async def abandon_game(db: AsyncSession, *, profile: Profile, game_id: UUID) -> Game:
        game = await GameService.get_game_for_user(db, profile=profile, game_id=game_id)
        if game.status != GameStatus.ACTIVE:
            raise ConflictError("Only active games can be abandoned.")
        game.status = GameStatus.ABANDONED
        game.finished_at = datetime.now(UTC)
        game.score = 0
        await db.commit()
        return await GameService.get_game_for_user(db, profile=profile, game_id=game_id)

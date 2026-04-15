from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.game import Game
from app.models.profile import Profile
from app.schemas.leaderboard import DailyLeaderboardEntry, LeaderboardEntry
from app.services.word_service import WordService
from app.utils.enums import GameMode, GameStatus


def rank_global_rows(rows: list[dict[str, Any]], *, offset: int = 0) -> list[LeaderboardEntry]:
    return [
        LeaderboardEntry(
            rank=offset + index + 1,
            user_id=row["user_id"],
            username=row.get("username"),
            total_score=int(row.get("total_score") or 0),
            wins=int(row.get("wins") or 0),
            total_games=int(row.get("total_games") or 0),
            average_attempts_on_wins=round(float(row["average_attempts_on_wins"]), 2)
            if row.get("average_attempts_on_wins") is not None
            else None,
        )
        for index, row in enumerate(rows)
    ]


def rank_daily_rows(rows: list[dict[str, Any]], *, offset: int = 0) -> list[DailyLeaderboardEntry]:
    return [
        DailyLeaderboardEntry(
            rank=offset + index + 1,
            user_id=row["user_id"],
            username=row.get("username"),
            score=int(row.get("score") or 0),
            attempts_used=int(row.get("attempts_used") or 0),
            finished_at=row.get("finished_at"),
            challenge_date=row["challenge_date"],
            word_length=int(row["word_length"]),
        )
        for index, row in enumerate(rows)
    ]


class LeaderboardService:
    @staticmethod
    async def global_leaderboard(db: AsyncSession, *, limit: int, offset: int) -> list[LeaderboardEntry]:
        rows = list(
            (
                await db.execute(
                    select(
                        Profile.id.label("user_id"),
                        Profile.username.label("username"),
                        func.coalesce(func.sum(Game.score), 0).label("total_score"),
                        func.coalesce(func.sum(case((Game.status == GameStatus.WON, 1), else_=0)), 0).label("wins"),
                        func.count(Game.id).label("total_games"),
                        func.avg(Game.attempts_used).filter(Game.status == GameStatus.WON).label("average_attempts_on_wins"),
                    )
                    .join(Game, Game.user_id == Profile.id)
                    .where(Game.status.in_([GameStatus.WON, GameStatus.LOST, GameStatus.ABANDONED]))
                    .group_by(Profile.id, Profile.username)
                    .order_by(
                        func.coalesce(func.sum(Game.score), 0).desc(),
                        func.coalesce(func.sum(case((Game.status == GameStatus.WON, 1), else_=0)), 0).desc(),
                        func.avg(Game.attempts_used).filter(Game.status == GameStatus.WON).asc().nullslast(),
                        Profile.username.asc().nullslast(),
                        Profile.id.asc(),
                    )
                    .limit(limit)
                    .offset(offset)
                )
            ).mappings()
        )
        return rank_global_rows([dict(row) for row in rows], offset=offset)

    @staticmethod
    async def by_length_leaderboard(
        db: AsyncSession,
        *,
        word_length: int,
        limit: int,
        offset: int,
    ) -> list[LeaderboardEntry]:
        WordService.ensure_allowed_length(word_length)
        rows = list(
            (
                await db.execute(
                    select(
                        Profile.id.label("user_id"),
                        Profile.username.label("username"),
                        func.coalesce(func.sum(Game.score), 0).label("total_score"),
                        func.coalesce(func.sum(case((Game.status == GameStatus.WON, 1), else_=0)), 0).label("wins"),
                        func.count(Game.id).label("total_games"),
                        func.avg(Game.attempts_used).filter(Game.status == GameStatus.WON).label("average_attempts_on_wins"),
                    )
                    .join(Game, Game.user_id == Profile.id)
                    .where(
                        Game.word_length == word_length,
                        Game.status.in_([GameStatus.WON, GameStatus.LOST, GameStatus.ABANDONED]),
                    )
                    .group_by(Profile.id, Profile.username)
                    .order_by(
                        func.coalesce(func.sum(Game.score), 0).desc(),
                        func.coalesce(func.sum(case((Game.status == GameStatus.WON, 1), else_=0)), 0).desc(),
                        func.avg(Game.attempts_used).filter(Game.status == GameStatus.WON).asc().nullslast(),
                        Profile.username.asc().nullslast(),
                        Profile.id.asc(),
                    )
                    .limit(limit)
                    .offset(offset)
                )
            ).mappings()
        )
        return rank_global_rows([dict(row) for row in rows], offset=offset)

    @staticmethod
    async def daily_leaderboard(
        db: AsyncSession,
        *,
        challenge_date: date,
        word_length: int,
        limit: int,
        offset: int,
    ) -> list[DailyLeaderboardEntry]:
        WordService.ensure_allowed_length(word_length)
        rows = list(
            (
                await db.execute(
                    select(
                        Profile.id.label("user_id"),
                        Profile.username.label("username"),
                        Game.score.label("score"),
                        Game.attempts_used.label("attempts_used"),
                        Game.finished_at.label("finished_at"),
                        Game.challenge_date.label("challenge_date"),
                        Game.word_length.label("word_length"),
                    )
                    .join(Game, Game.user_id == Profile.id)
                    .where(
                        Game.mode == GameMode.DAILY,
                        Game.status == GameStatus.WON,
                        Game.challenge_date == challenge_date,
                        Game.word_length == word_length,
                    )
                    .order_by(
                        Game.score.desc(),
                        Game.attempts_used.asc(),
                        Game.finished_at.asc().nullslast(),
                        Profile.username.asc().nullslast(),
                        Profile.id.asc(),
                    )
                    .limit(limit)
                    .offset(offset)
                )
            ).mappings()
        )
        return rank_daily_rows([dict(row) for row in rows], offset=offset)

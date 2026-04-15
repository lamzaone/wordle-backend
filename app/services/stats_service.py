from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.game import Game
from app.schemas.profile import StatsSummary
from app.utils.enums import GameStatus


class StatsService:
    @staticmethod
    async def get_user_stats(db: AsyncSession, *, user_id: UUID) -> StatsSummary:
        aggregate = (
            await db.execute(
                select(
                    func.count(Game.id).filter(Game.status != GameStatus.ACTIVE).label("total_games"),
                    func.count(Game.id).filter(Game.status == GameStatus.WON).label("wins"),
                    func.count(Game.id).filter(Game.status == GameStatus.LOST).label("losses"),
                    func.coalesce(func.sum(Game.score), 0).label("total_score"),
                    func.avg(Game.attempts_used).filter(Game.status == GameStatus.WON).label("avg_attempts"),
                ).where(Game.user_id == user_id)
            )
        ).one()

        streak_rows = list(
            (
                await db.execute(
                    select(Game.status)
                    .where(Game.user_id == user_id, Game.status != GameStatus.ACTIVE)
                    .order_by(Game.finished_at.asc().nullslast(), Game.created_at.asc())
                )
            ).scalars()
        )

        current_streak = 0
        for status in reversed(streak_rows):
            if status == GameStatus.WON:
                current_streak += 1
            else:
                break

        best_streak = 0
        running = 0
        for status in streak_rows:
            if status == GameStatus.WON:
                running += 1
                best_streak = max(best_streak, running)
            else:
                running = 0

        wins = int(aggregate.wins or 0)
        losses = int(aggregate.losses or 0)
        decisive_games = wins + losses
        win_rate = round((wins / decisive_games) * 100, 2) if decisive_games else 0.0

        return StatsSummary(
            total_games=int(aggregate.total_games or 0),
            wins=wins,
            losses=losses,
            win_rate=win_rate,
            current_streak=current_streak,
            best_streak=best_streak,
            average_attempts_on_wins=round(float(aggregate.avg_attempts), 2) if aggregate.avg_attempts is not None else None,
            total_score=int(aggregate.total_score or 0),
        )

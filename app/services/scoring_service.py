from __future__ import annotations

from app.core.config import Settings, get_settings
from app.utils.enums import GameMode


def calculate_score(
    *,
    word_length: int,
    max_attempts: int,
    attempts_used: int,
    won: bool,
    mode: GameMode,
    settings: Settings | None = None,
) -> int:
    if not won:
        return 0

    active_settings = settings or get_settings()
    base_score = active_settings.score_base_by_length.get(word_length, word_length * 20)
    remaining_attempts = max(max_attempts - attempts_used, 0)
    score = base_score + active_settings.score_win_bonus
    score += remaining_attempts * active_settings.score_remaining_attempt_bonus
    if mode == GameMode.DAILY:
        score += active_settings.score_daily_bonus
    return max(score, 0)

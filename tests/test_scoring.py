from app.core.config import get_settings
from app.services.scoring_service import calculate_score
from app.utils.enums import GameMode


def test_score_rewards_fewer_attempts():
    settings = get_settings()
    early = calculate_score(
        word_length=5,
        max_attempts=6,
        attempts_used=2,
        won=True,
        mode=GameMode.CLASSIC,
        settings=settings,
    )
    late = calculate_score(
        word_length=5,
        max_attempts=6,
        attempts_used=6,
        won=True,
        mode=GameMode.CLASSIC,
        settings=settings,
    )
    assert early > late > 0


def test_daily_win_gets_bonus():
    settings = get_settings()
    classic = calculate_score(
        word_length=5,
        max_attempts=6,
        attempts_used=3,
        won=True,
        mode=GameMode.CLASSIC,
        settings=settings,
    )
    daily = calculate_score(
        word_length=5,
        max_attempts=6,
        attempts_used=3,
        won=True,
        mode=GameMode.DAILY,
        settings=settings,
    )
    assert daily == classic + settings.score_daily_bonus


def test_loss_scores_zero():
    assert (
        calculate_score(
            word_length=5,
            max_attempts=6,
            attempts_used=6,
            won=False,
            mode=GameMode.CLASSIC,
        )
        == 0
    )

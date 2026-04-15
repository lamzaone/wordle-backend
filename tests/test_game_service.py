from app.core.config import get_settings
from app.services.errors import ValidationServiceError
from app.services.game_service import resolve_guess_state
from app.utils.enums import GameMode, GameStatus
import pytest


def test_resolve_guess_marks_win_and_scores():
    resolution = resolve_guess_state(
        target_word="crane",
        guess="crane",
        word_length=5,
        current_attempts=1,
        max_attempts=6,
        mode=GameMode.CLASSIC,
        settings=get_settings(),
    )
    assert resolution.status == GameStatus.WON
    assert resolution.attempts_used == 2
    assert resolution.is_correct is True
    assert resolution.score > 0
    assert resolution.finished_at is not None


def test_resolve_guess_marks_loss_on_final_attempt():
    resolution = resolve_guess_state(
        target_word="crane",
        guess="sloth",
        word_length=5,
        current_attempts=5,
        max_attempts=6,
        mode=GameMode.CLASSIC,
        settings=get_settings(),
    )
    assert resolution.status == GameStatus.LOST
    assert resolution.attempts_used == 6
    assert resolution.score == 0
    assert resolution.finished_at is not None


def test_resolve_guess_rejects_wrong_length():
    with pytest.raises(ValidationServiceError):
        resolve_guess_state(
            target_word="crane",
            guess="car",
            word_length=5,
            current_attempts=0,
            max_attempts=6,
            mode=GameMode.CLASSIC,
            settings=get_settings(),
        )

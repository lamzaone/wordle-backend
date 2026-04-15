from datetime import UTC, date, datetime
from uuid import UUID

from app.services.leaderboard_service import rank_daily_rows, rank_global_rows


def test_rank_global_rows_applies_offset_and_metrics():
    rows = [
        {
            "user_id": UUID("00000000-0000-0000-0000-000000000001"),
            "username": "ada",
            "total_score": 320,
            "wins": 3,
            "total_games": 4,
            "average_attempts_on_wins": 3.333,
        }
    ]
    ranked = rank_global_rows(rows, offset=20)
    assert ranked[0].rank == 21
    assert ranked[0].username == "ada"
    assert ranked[0].average_attempts_on_wins == 3.33


def test_rank_daily_rows_exposes_no_hidden_word_fields():
    rows = [
        {
            "user_id": UUID("00000000-0000-0000-0000-000000000001"),
            "username": "ada",
            "score": 155,
            "attempts_used": 3,
            "finished_at": datetime(2026, 1, 1, tzinfo=UTC),
            "challenge_date": date(2026, 1, 1),
            "word_length": 5,
        }
    ]
    ranked = rank_daily_rows(rows)
    data = ranked[0].model_dump()
    assert data["rank"] == 1
    assert "word" not in data
    assert "word_id" not in data

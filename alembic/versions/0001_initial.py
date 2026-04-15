from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("username", sa.String(length=32), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_profiles")),
        sa.UniqueConstraint("username", name=op.f("uq_profiles_username")),
    )
    op.create_index(op.f("ix_profiles_username"), "profiles", ["username"], unique=True)

    op.create_table(
        "words",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("value", sa.String(length=32), nullable=False),
        sa.Column("length", sa.Integer(), nullable=False),
        sa.Column("language", sa.String(length=8), server_default="en", nullable=False),
        sa.Column("difficulty", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("length > 0", name=op.f("ck_words_length_positive")),
        sa.CheckConstraint("difficulty IS NULL OR difficulty BETWEEN 1 AND 10", name=op.f("ck_words_difficulty_range")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_words")),
        sa.UniqueConstraint("value", "language", name="uq_words_value_language"),
    )
    op.create_index(op.f("ix_words_length"), "words", ["length"], unique=False)
    op.create_index("ix_words_length_language_active", "words", ["length", "language", "is_active"], unique=False)

    op.create_table(
        "games",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("word_id", sa.Integer(), nullable=False),
        sa.Column("word_length", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("max_attempts", sa.Integer(), nullable=False),
        sa.Column("attempts_used", sa.Integer(), server_default="0", nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("score", sa.Integer(), server_default="0", nullable=False),
        sa.Column("mode", sa.String(length=16), nullable=False),
        sa.Column("challenge_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("word_length > 0", name=op.f("ck_games_word_length_positive")),
        sa.CheckConstraint("max_attempts > 0", name=op.f("ck_games_max_attempts_positive")),
        sa.CheckConstraint("attempts_used >= 0", name=op.f("ck_games_attempts_used_nonnegative")),
        sa.CheckConstraint("score >= 0", name=op.f("ck_games_score_nonnegative")),
        sa.CheckConstraint("status IN ('active', 'won', 'lost', 'abandoned')", name=op.f("ck_games_status_values")),
        sa.CheckConstraint("mode IN ('classic', 'daily')", name=op.f("ck_games_mode_values")),
        sa.ForeignKeyConstraint(["user_id"], ["profiles.id"], name=op.f("fk_games_user_id_profiles"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["word_id"], ["words.id"], name=op.f("fk_games_word_id_words"), ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_games")),
    )
    op.create_index("ix_games_daily", "games", ["mode", "challenge_date", "word_length"], unique=False)
    op.create_index("ix_games_leaderboard", "games", ["status", "word_length", "score"], unique=False)
    op.create_index("ix_games_user_mode_length", "games", ["user_id", "mode", "word_length"], unique=False)
    op.create_index("ix_games_user_status", "games", ["user_id", "status"], unique=False)

    op.create_table(
        "daily_challenges",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("challenge_date", sa.Date(), nullable=False),
        sa.Column("word_length", sa.Integer(), nullable=False),
        sa.Column("word_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("word_length > 0", name=op.f("ck_daily_challenges_word_length_positive")),
        sa.ForeignKeyConstraint(["word_id"], ["words.id"], name=op.f("fk_daily_challenges_word_id_words"), ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_daily_challenges")),
        sa.UniqueConstraint("challenge_date", "word_length", name="uq_daily_challenges_date_length"),
    )
    op.create_index(op.f("ix_daily_challenges_challenge_date"), "daily_challenges", ["challenge_date"], unique=False)
    op.create_index(op.f("ix_daily_challenges_word_length"), "daily_challenges", ["word_length"], unique=False)

    op.create_table(
        "guesses",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("game_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("guess_value", sa.String(length=32), nullable=False),
        sa.Column("result_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("attempt_number > 0", name=op.f("ck_guesses_attempt_number_positive")),
        sa.ForeignKeyConstraint(["game_id"], ["games.id"], name=op.f("fk_guesses_game_id_games"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_guesses")),
        sa.UniqueConstraint("game_id", "attempt_number", name="uq_guesses_game_attempt"),
    )
    op.create_index(op.f("ix_guesses_game_id"), "guesses", ["game_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_guesses_game_id"), table_name="guesses")
    op.drop_table("guesses")
    op.drop_index(op.f("ix_daily_challenges_word_length"), table_name="daily_challenges")
    op.drop_index(op.f("ix_daily_challenges_challenge_date"), table_name="daily_challenges")
    op.drop_table("daily_challenges")
    op.drop_index("ix_games_user_status", table_name="games")
    op.drop_index("ix_games_user_mode_length", table_name="games")
    op.drop_index("ix_games_leaderboard", table_name="games")
    op.drop_index("ix_games_daily", table_name="games")
    op.drop_table("games")
    op.drop_index("ix_words_length_language_active", table_name="words")
    op.drop_index(op.f("ix_words_length"), table_name="words")
    op.drop_table("words")
    op.drop_index(op.f("ix_profiles_username"), table_name="profiles")
    op.drop_table("profiles")

from __future__ import annotations

from alembic import op

revision = "0002_enable_rls"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


TABLES = (
    "alembic_version",
    "profiles",
    "words",
    "games",
    "guesses",
    "daily_challenges",
)


def upgrade() -> None:
    for table in TABLES:
        op.execute(f"ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY")

    op.execute(
        """
        COMMENT ON TABLE public.profiles IS
        'Application table. Direct client REST access is blocked by RLS; FastAPI is the trusted data access layer.'
        """
    )
    op.execute(
        """
        COMMENT ON TABLE public.words IS
        'Application dictionary. Direct client REST access is blocked by RLS; FastAPI manages game logic and admin word writes.'
        """
    )
    op.execute(
        """
        COMMENT ON TABLE public.games IS
        'Game state table. Direct client REST access is blocked by RLS; FastAPI owns hidden words, status, and scoring.'
        """
    )
    op.execute(
        """
        COMMENT ON TABLE public.guesses IS
        'Guess history table. Direct client REST access is blocked by RLS; FastAPI validates and stores guesses.'
        """
    )
    op.execute(
        """
        COMMENT ON TABLE public.daily_challenges IS
        'Daily challenge table. Direct client REST access is blocked by RLS; FastAPI manages daily generation.'
        """
    )


def downgrade() -> None:
    for table in reversed(TABLES):
        op.execute(f"ALTER TABLE public.{table} DISABLE ROW LEVEL SECURITY")

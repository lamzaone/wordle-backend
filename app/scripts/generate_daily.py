from __future__ import annotations

import argparse
import asyncio
from datetime import date

from app.core.config import get_settings
from app.db.session import AsyncSessionLocal
from app.services.daily_service import DailyChallengeService


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate daily Wordle challenges in Supabase Cloud Postgres.")
    parser.add_argument("--date", dest="challenge_date", type=date.fromisoformat, default=None)
    parser.add_argument("--length", dest="word_lengths", type=int, action="append", required=True)
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    settings = get_settings()
    challenge_date = args.challenge_date or DailyChallengeService.current_challenge_date(settings)
    async with AsyncSessionLocal() as db:
        for word_length in args.word_lengths:
            challenge = await DailyChallengeService.get_or_create_challenge(
                db,
                challenge_date=challenge_date,
                word_length=word_length,
                settings=settings,
            )
            print(f"Generated daily challenge {challenge.challenge_date} length={challenge.word_length}")


if __name__ == "__main__":
    asyncio.run(main())

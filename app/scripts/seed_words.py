from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from app.core.config import get_settings
from app.db.session import AsyncSessionLocal
from app.services.word_service import WordService


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed words into Supabase Cloud Postgres.")
    parser.add_argument("--file", required=True, help="Path to a newline-delimited word list.")
    parser.add_argument("--language", default="en")
    parser.add_argument("--difficulty", type=int, default=None)
    parser.add_argument("--inactive", action="store_true", help="Seed words as inactive.")
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    settings = get_settings()
    path = Path(args.file)
    words = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    async with AsyncSessionLocal() as db:
        created = await WordService.bulk_import(
            db,
            words=words,
            language=args.language,
            difficulty=args.difficulty,
            is_active=not args.inactive,
            settings=settings,
        )
    print(f"Seeded {len(created)} new words into Supabase Cloud Postgres.")


if __name__ == "__main__":
    asyncio.run(main())

from __future__ import annotations

import re
from collections import Counter

from app.utils.enums import GuessLetterStatus

WORD_PATTERN = re.compile(r"^[a-z]+$")


class WordValidationError(ValueError):
    pass


def normalize_word(value: str) -> str:
    return value.strip().lower()


def validate_word_value(value: str, *, expected_length: int | None = None, allowed_lengths: list[int] | None = None) -> str:
    normalized = normalize_word(value)
    if not normalized or not WORD_PATTERN.fullmatch(normalized):
        raise WordValidationError("Words must contain only ASCII letters a-z.")
    if expected_length is not None and len(normalized) != expected_length:
        raise WordValidationError(f"Word must be exactly {expected_length} letters.")
    if allowed_lengths is not None and len(normalized) not in allowed_lengths:
        lengths = ", ".join(str(length) for length in allowed_lengths)
        raise WordValidationError(f"Word length must be one of: {lengths}.")
    return normalized


def evaluate_guess(target: str, guess: str) -> list[dict[str, str]]:
    target_value = normalize_word(target)
    guess_value = normalize_word(guess)
    if len(target_value) != len(guess_value):
        raise WordValidationError("Guess and target must have the same length.")

    result: list[dict[str, str]] = [
        {"letter": letter, "status": GuessLetterStatus.ABSENT.value}
        for letter in guess_value
    ]

    unmatched_target_letters: Counter[str] = Counter()
    for index, target_letter in enumerate(target_value):
        if guess_value[index] == target_letter:
            result[index]["status"] = GuessLetterStatus.CORRECT.value
        else:
            unmatched_target_letters[target_letter] += 1

    for index, guess_letter in enumerate(guess_value):
        if result[index]["status"] == GuessLetterStatus.CORRECT.value:
            continue
        if unmatched_target_letters[guess_letter] > 0:
            result[index]["status"] = GuessLetterStatus.PRESENT.value
            unmatched_target_letters[guess_letter] -= 1

    return result

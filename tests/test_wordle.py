import pytest

from app.utils.wordle import WordValidationError, evaluate_guess, validate_word_value


def statuses(result):
    return [item["status"] for item in result]


def test_evaluate_guess_all_correct():
    result = evaluate_guess("crane", "crane")
    assert statuses(result) == ["correct", "correct", "correct", "correct", "correct"]


def test_evaluate_guess_handles_duplicate_letters_without_overcounting():
    result = evaluate_guess("apple", "allee")
    assert statuses(result) == ["correct", "present", "absent", "absent", "correct"]


def test_evaluate_guess_handles_multiple_duplicate_letters():
    result = evaluate_guess("civic", "icici")
    assert statuses(result) == ["present", "present", "present", "present", "absent"]


def test_validate_word_rejects_invalid_characters():
    with pytest.raises(WordValidationError):
        validate_word_value("bad-word")


def test_validate_word_rejects_wrong_length():
    with pytest.raises(WordValidationError):
        validate_word_value("crane", expected_length=4)

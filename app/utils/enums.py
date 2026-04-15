from enum import Enum


class GameStatus(str, Enum):
    ACTIVE = "active"
    WON = "won"
    LOST = "lost"
    ABANDONED = "abandoned"


class GameMode(str, Enum):
    CLASSIC = "classic"
    DAILY = "daily"


class GuessLetterStatus(str, Enum):
    CORRECT = "correct"
    PRESENT = "present"
    ABSENT = "absent"

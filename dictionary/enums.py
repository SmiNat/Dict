from enum import Enum


class WordTypes(str, Enum):
    def __new__(cls, value: str, translation: str):
        obj = str.__new__(cls, value)
        obj._value_ = value
        obj.translation = translation
        return obj

    @classmethod
    def list_of_values(cls) -> list[str]:
        return list(map(lambda c: c.value, cls))

    NOUN = "noun", "rzeczownik"
    VERB = "verb", "czasownik"
    ADJECTIVE = "adjective", "przymiotnik"
    NUMERAL = "numeral", "liczebnik"
    PRONOUN = "pronoun", "zaimek"
    ADVERB = "averb", "przysłówek"
    PREPOSITION = "preposition", "przyimek"
    PARTICLE = "particle", "partykuła"
    CONJUNCTION = "conjunction", "spójnik"
    INTERJECTION = "interjection", "wykrzyknik"
    IDIOM = "idiom", "idiom"


class MasterLevel(str, Enum):
    def __new__(cls, value: str, weight: float | int):
        obj = str.__new__(cls, value)
        obj._value_ = value  # The string label (e.g., "new", "medium")
        obj.weight = weight  # The float weight (e.g., 1.0, 0.8)
        return obj

    @classmethod
    def list_of_values(cls) -> list[str]:
        return list(map(lambda c: c.value, cls))

    NEW = "new", 1.0
    MEDIUM = "medium", 0.8
    PERFECT = "prefect", 0.3
    HARD = "hard", 1.5

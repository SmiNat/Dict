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

    NOUN = "noun", "rzeczownik"  # kto? co?
    VERB = (
        "verb",
        "czasownik",
    )  # co robi? co się z nim dzieje? w jakim stanie się znajduje?
    ADJECTIVE = (
        "adjective",
        "przymiotnik",
    )  # jaki? jaka? jakie? czyj? czyja? czyje? który? która? które? (wyraz określający cechy, właściwości istot żywych, rzeczy, zjawisk), np. purpurowy, duży, daleki;
    NUMERAL = (
        "numeral",
        "liczebnik",
    )  # ile? który z kolei? (wskazuje na liczbę lub porządek ludzi i rzeczy), np. cztery, dwunasty, troje;
    PRONOUN = (
        "pronoun",
        "zaimek",
    )  # zastępuje inne części mowy (rzeczownik, przysłówek, przymiotnik, liczebnik) i wyraża ich treść np. twój, jego, mój, tam, kto;
    ADVERB = (
        "averb",
        "przysłówek",
    )  # jak? gdzie? kiedy? (określenie właściwości, cech czynności), np. długo, daleko, wczoraj;
    PREPOSITION = (
        "preposition",
        "przyimek",
    )  # łączy się z innymi częściami mowy (najczęściej z rzeczownikiem), nadając im nowy sens, np. nad, za, w, ponad, przed, po;
    PARTICLE = (
        "particle",
        "partykuła",
    )  # stosuje się ją do wyrażania lub podkreślenia emocji, np. niech, właśnie, tylko, ani;
    CONJUNCTION = (
        "conjunction",
        "spójnik",
    )  # łączy zdania lub wyrażenia, np. albo, więc, oraz, i, aby, bo;
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


# class MasterLevel(str, Enum):
#     @classmethod
#     def list_of_values(cls):
#         return list(map(lambda c: c.value, cls))

#     NEW = "new"
#     MEDIUM = "medium"
#     PERFECT = "prefect"
#     HARD = "hard"


# class MasterLevelWeight(Enum):
#     @classmethod
#     def list_of_values(cls):
#         return list(map(lambda c: c.value, cls))

#     NEW = 1.0
#     MEDIUM = 0.8
#     PERFECT = 0.3
#     HARD = 1.5

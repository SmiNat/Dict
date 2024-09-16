from enum import Enum


class WordTypes(str, Enum):
    def __new__(cls, value, translation):
        obj = str.__new__(cls, value)
        obj._value_ = value
        obj.translation = translation
        return obj

    @classmethod
    def list_of_values(cls):
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
    @classmethod
    def list_of_values(cls):
        return list(map(lambda c: c.value, cls))

    NEW = "new"
    MEDIUM = "medium"
    PERFECT = "prefect"
    HARD = "hard"

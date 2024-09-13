from dictionary.enums import MasterLevel, WordTypes
from dictionary.models import Description, Word, WordDescription
from dictionary.tests.conftest import TestingSessionLocal


def create_word(
    word: str = "pivot",
    master_level: str = MasterLevel.NEW,
    notes: str = None,
) -> Word:
    """Helper function to create a word in the test database.
    NOTE: We use TestingSessionLocal instead of db_session fixture to overcome \
        the issue of cleaning the database after each function usage.
    """
    db = TestingSessionLocal()
    new_word = Word(word=word, master_level=master_level, notes=notes)
    try:
        db.add(new_word)
        db.commit()
        db.refresh(new_word)
        return new_word
    finally:
        db.close()


def create_description(
    type: str = WordTypes.NOUN,
    in_polish: str = "sedno",
    in_english: str | None = None,
    example: str | None = None,
) -> Description:
    """Helper function to create a description in the test database.
    NOTE: We use TestingSessionLocal instead of db_session fixture to overcome \
        the issue of cleaning the database after each function usage.
    """
    db = TestingSessionLocal()
    new_desc = Description(
        type=type, in_polish=in_polish, in_english=in_english, example=example
    )
    try:
        db.add(new_desc)
        db.commit()
        db.refresh(new_desc)
        return new_desc
    finally:
        db.close()


def create_word_definition_association_table(
    word_id: int, description_id: int
) -> WordDescription:
    """Helper function to create a word-description in the test database.
    NOTE: We use TestingSessionLocal instead of db_session fixture to overcome \
        the issue of cleaning the database after each function usage.
    """
    db = TestingSessionLocal()
    word_desc = WordDescription(word_id=word_id, description_id=description_id)
    try:
        db.add(word_desc)
        db.commit()
        db.refresh(word_desc)
        return word_desc
    finally:
        db.close()

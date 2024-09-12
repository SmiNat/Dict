from sqlalchemy.orm import Session

from dictionary.enums import MasterLevel
from dictionary.models import Word


def create_word(
    db: Session,
    word: str = "pivot",
    master_level: str = MasterLevel.NEW,
    notes: str = None,
):
    new_word = Word(word=word, master_level=master_level, notes=notes)
    db.add(new_word)
    db.commit()
    db.refresh(new_word)
    return new_word


def test_create_word(db_session):
    # Use db_session provided by the fixture
    word = create_word(db_session, word="pivot on sth", master_level=MasterLevel.NEW)

    assert word.word == "pivot on sth"
    assert word.master_level == MasterLevel.NEW

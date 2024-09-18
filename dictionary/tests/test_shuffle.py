import logging
from unittest.mock import patch

import pytest
from sqlalchemy.orm import Session

from dictionary.enums import MasterLevel
from dictionary.exceptions import DatabaseError
from dictionary.models import LevelWeight
from dictionary.routers.shuffle import Shuffle

logger = logging.getLogger(__name__)


def test_database_levels_method_successful(db_session: Session):
    # Empty db table
    levels = db_session.query(LevelWeight).all()
    assert levels == []

    # After calling database_levels() method which populates db table
    expected_levels = MasterLevel.list_of_values()
    expected_default_weights = [level.weight for level in MasterLevel]
    expected_new_weights = [None, None, None, None]

    response = Shuffle.database_levels(db_session)

    assert expected_levels == [x.level for x in response]
    assert expected_default_weights == [x.default_weight for x in response]
    assert expected_new_weights == [x.new_weight for x in response]


def test_update_recent_words_method_successful():
    expected_initial_value = []
    assert Shuffle.recent_words == expected_initial_value

    # Calling method - first call
    Shuffle._update_recent_words(word="test")
    assert Shuffle.recent_words == ["test"]

    # Calling method - second and third call
    # - descending order (last word added is first on the list)
    Shuffle._update_recent_words("test2")
    Shuffle._update_recent_words("test3")
    assert Shuffle.recent_words == ["test3", "test2", "test"]

    # Calling method - 4th call
    # - up to 3 words in the list (most recent)
    Shuffle._update_recent_words("test4")
    assert Shuffle.recent_words == ["test4", "test3", "test2"]


def test_update_recent_words_method_valueerror_with_word_already_on_the_list():
    with patch.object(Shuffle, "recent_words", ["test", "test2", "test3"]):
        with pytest.raises(ValueError) as exc_info:
            Shuffle._update_recent_words(word="test")

    assert "The word/sentence 'test' is already on the list." == str(exc_info.value)


def test_update_level_method_successful(db_session: Session):
    # Empty db table
    levels = db_session.query(LevelWeight).all()
    assert levels == []

    valid_input_data = {"level": MasterLevel.HARD, "value": 2.5}

    # After calling update_level() method
    Shuffle.update_level(db=db_session, **valid_input_data)

    levels = db_session.query(LevelWeight).all()

    expected_levels = MasterLevel.list_of_values()
    expected_default_weights = [level.weight for level in MasterLevel]
    expected_new_weights = [None, None, None, valid_input_data["value"]]

    assert expected_levels == [x.level for x in levels]
    assert expected_default_weights == [x.default_weight for x in levels]
    assert expected_new_weights == [x.new_weight for x in levels]


def test_update_level_method_databaseerror_if_no_levels_in_level_weight_table(
    db_session: Session,
):
    valid_input_data = {"level": MasterLevel.HARD, "value": 2.5}

    with patch.object(Shuffle, "database_levels"):
        with pytest.raises(DatabaseError) as exc_info:
            Shuffle.update_level(db=db_session, **valid_input_data)
    assert exc_info.value.status_code == 404
    assert (
        f"No '{valid_input_data["level"].value}' level found in the database."
        in exc_info.value.message
    )


def test_update_level_method_valueerror_if_invalid_input_value(
    db_session: Session,
):
    invalid_input_data = {"level": MasterLevel.HARD, "value": 999}

    with pytest.raises(ValueError) as exc_info:
        Shuffle.update_level(db=db_session, **invalid_input_data)

    assert "The acceptable value range is from 0 to 5.0." == str(exc_info.value)


def test_update_level_method_databaseerror_if_invalid_input_value(
    db_session: Session,
):
    invalid_input_data = {"level": "invalid", "value": 2.5}

    with pytest.raises(DatabaseError) as exc_info:
        Shuffle.update_level(db=db_session, **invalid_input_data)

    assert "Invalid level name. Acceptable levels:" in exc_info.value.message


def test_fetch_word_successful(db_session: Session):
    pass

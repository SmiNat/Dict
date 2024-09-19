import logging
from unittest.mock import patch

import pytest
from fastapi import HTTPException  # noqa
from httpx import AsyncClient
from sqlalchemy.orm import Session

from dictionary.enums import MasterLevel
from dictionary.exceptions import DatabaseError
from dictionary.models import LevelWeight
from dictionary.routers.shuffle import Shuffle
from dictionary.tests.utils import create_description, create_word

logger = logging.getLogger(__name__)


def test_database_levels_method_successful(db_session: Session):
    # Empty db table
    levels = db_session.query(LevelWeight).all()
    assert levels == []

    # Calling database_levels method which populates db table
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
    # descending order (last word added is the first on the list)
    Shuffle._update_recent_words("test2")
    Shuffle._update_recent_words("test3")
    assert Shuffle.recent_words == ["test3", "test2", "test"]

    # Calling method - 4th call
    # up to 3 words in the list (most recent)
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

    # Calling update_level method
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
    invalid_input_data = {"level": MasterLevel.HARD, "value": 999}  # valid range 0-5

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
    assert 400 == exc_info.value.status_code


def test_fetch_word_method_successful_with_up_to_3_words_in_db(db_session: Session):
    Shuffle.recent_words = []
    word_1 = create_word()
    word_2 = create_word("test")

    fetched_word = Shuffle.fetch_word(db_session)
    assert fetched_word[1] in [word_1.word, word_2.word]
    assert Shuffle.recent_words == [fetched_word[1]]


def test_fetch_word_method_successful_with_more_than_3_words_in_db(db_session: Session):
    Shuffle.recent_words = []
    for x in range(4):
        create_word("test{}".format(x))

    last_words = []
    for _ in range(30):
        word_list = last_words[:3]
        fetched_word = Shuffle.fetch_word(db_session)
        word_list.insert(0, fetched_word[1])
        last_words = word_list[:3]
        assert sorted(Shuffle.recent_words) == sorted(list(set(Shuffle.recent_words)))
        assert Shuffle.recent_words == last_words


def test_fetch_word_method_empty_word_table_in_db(db_session: Session):
    expected_message = "No words found in the database."

    with pytest.raises(DatabaseError) as exc_info:
        Shuffle.fetch_word(db_session)

    assert expected_message == str(exc_info.value)
    assert 404 == exc_info.value.status_code


def test_fetch_word_method_empty_levelweight_table_in_db(db_session: Session):
    create_word()  # fillilng words table with initial data
    expected_message = "No levels specified in the database."

    with patch.object(Shuffle, "database_levels") as mocked_levels:
        mocked_levels.return_value = []
        with pytest.raises(DatabaseError) as exc_info:
            Shuffle.fetch_word(db_session)

    assert expected_message == exc_info.value.message
    assert 404 == exc_info.value.status_code


def test_fetch_description_method_successful(db_session: Session):
    Shuffle.last_description = ""
    create_description(in_polish="new")
    create_description(in_polish="test")
    create_description(in_polish="abc")

    for _ in range(20):
        last_desc = Shuffle.last_description
        desc = Shuffle.fetch_description(db_session)
        assert desc != last_desc


def test_fetch_description_method_empty_db(db_session: Session):
    expected_message = "No descriptions found in the database."

    with pytest.raises(DatabaseError) as exc_info:
        Shuffle.fetch_description(db_session)

    assert expected_message == exc_info.value.message
    assert 404 == exc_info.value.status_code


@pytest.mark.anyio
async def test_get_all_levels_endpoint_successful_with_no_new_weights(
    db_session: Session, async_client: AsyncClient
):
    expected_response = []
    for x in range(len(MasterLevel)):
        expected_response.append(
            {
                "level": MasterLevel.list_of_values()[x],
                "default_weight": MasterLevel.list_of_weights()[x],
                "new_weight": None,
            }
        )

    response = await async_client.get("/shuffle/all_levels")
    assert response.status_code == 200
    assert response.json() == {"levels": expected_response}


@pytest.mark.anyio
async def test_get_all_levels_endpoint_successful_with_new_weights(
    db_session: Session, async_client: AsyncClient
):
    new_weight = {"level": MasterLevel.HARD, "value": 3.1}
    Shuffle.update_level(db_session, new_weight["level"], value=new_weight["value"])
    expected_response = []
    for x in range(len(MasterLevel)):
        expected_response.append(
            {
                "level": MasterLevel.list_of_values()[x],
                "default_weight": MasterLevel.list_of_weights()[x],
                "new_weight": new_weight["value"]
                if MasterLevel.list_of_values()[x] == new_weight["level"]
                else None,
            }
        )

    response = await async_client.get("/shuffle/all_levels")
    assert response.status_code == 200
    assert response.json() == {"levels": expected_response}


@pytest.mark.anyio
async def test_update_level_weight_endpoint_successful_empty_db(
    db_session: Session, async_client: AsyncClient
):
    level_hard = db_session.query(LevelWeight).filter_by(level=MasterLevel.HARD).first()
    assert level_hard is None

    payload = {"level": MasterLevel.HARD.value, "value": 3.3}

    await async_client.post("/shuffle/lvl_weight/update", params=payload)

    level_hard = db_session.query(LevelWeight).filter_by(level=MasterLevel.HARD).first()
    assert level_hard.default_weight == MasterLevel.HARD.weight
    assert level_hard.new_weight == payload["value"]


@pytest.mark.anyio
async def test_update_level_weight_endpoint_successful_not_empty_db(
    db_session: Session, async_client: AsyncClient
):
    Shuffle.database_levels(db_session)
    level_hard = db_session.query(LevelWeight).filter_by(level=MasterLevel.HARD).first()
    assert level_hard is not None
    assert level_hard.default_weight == MasterLevel.HARD.weight
    assert level_hard.new_weight is None

    payload = {"level": MasterLevel.HARD.value, "value": 3.3}

    await async_client.post("/shuffle/lvl_weight/update", params=payload)

    level_hard = db_session.query(LevelWeight).filter_by(level=MasterLevel.HARD).first()
    assert level_hard.default_weight == MasterLevel.HARD.weight
    assert level_hard.new_weight == payload["value"]


@pytest.mark.anyio
async def test_update_level_weight_endpoint_422_with_incorrect_weight_value(
    db_session: Session, async_client: AsyncClient
):
    Shuffle.database_levels(db_session)
    level_hard = db_session.query(LevelWeight).filter_by(level=MasterLevel.HARD).first()
    assert level_hard is not None
    assert level_hard.default_weight == MasterLevel.HARD.weight
    assert level_hard.new_weight is None

    expected_message = "Input should be less than or equal to 5"
    payload_invalid_value = {"level": MasterLevel.HARD.value, "value": 777}

    response = await async_client.post(
        "/shuffle/lvl_weight/update", params=payload_invalid_value
    )

    level_hard = db_session.query(LevelWeight).filter_by(level=MasterLevel.HARD).first()
    assert level_hard.default_weight == MasterLevel.HARD.weight
    assert level_hard.new_weight is None
    assert response.status_code == 422
    assert response.json()["detail"][0]["msg"] == expected_message


@pytest.mark.anyio
async def test_update_level_weight_endpoint_422_with_invalid_level(
    db_session: Session, async_client: AsyncClient
):
    Shuffle.database_levels(db_session)
    level_hard = db_session.query(LevelWeight).filter_by(level=MasterLevel.HARD).first()
    assert level_hard is not None
    assert level_hard.default_weight == MasterLevel.HARD.weight
    assert level_hard.new_weight is None

    expected_message = "Input should be 'new', 'medium', 'prefect' or 'hard'"
    payload_invalid_value = {"level": "invalid", "value": 3.1}

    response = await async_client.post(
        "/shuffle/lvl_weight/update", params=payload_invalid_value
    )

    level_hard = db_session.query(LevelWeight).filter_by(level=MasterLevel.HARD).first()
    assert level_hard.default_weight == MasterLevel.HARD.weight
    assert level_hard.new_weight is None
    assert response.status_code == 422
    assert response.json()["detail"][0]["msg"] == expected_message


@pytest.mark.anyio
async def test_get_random_word_successful(
    db_session: Session, async_client: AsyncClient
):
    with patch.object(Shuffle, "fetch_word") as mocked_word:
        mocked_word.return_value = (1, "test")
        response = await async_client.get("/shuffle/random_word")

    assert response.status_code == 200
    assert response.json() == {"word": "test", "id": 1}


@pytest.mark.anyio
async def test_get_random_word_404_empty_words_table_in_db(
    db_session: Session, async_client: AsyncClient
):
    expected_message = "No words found in the database."
    response = await async_client.get("/shuffle/random_word")

    assert response.status_code == 404
    assert response.json()["detail"] == expected_message


@pytest.mark.anyio
async def test_get_random_word_404_empty_levelweight_table_in_db(
    db_session: Session, async_client: AsyncClient
):
    create_word()
    expected_message = "No levels specified in the database."
    with patch.object(Shuffle, "database_levels") as mocked_levels:
        mocked_levels.return_value = []
        response = await async_client.get("/shuffle/random_word")

    assert response.status_code == 404
    assert response.json()["detail"] == expected_message


@pytest.mark.anyio
async def test_get_random_description_successful(
    db_session: Session, async_client: AsyncClient
):
    with patch.object(Shuffle, "fetch_description") as mocked_desc:
        mocked_desc.return_value = (1, "test")
        response = await async_client.get("/shuffle/random_desc")

    assert response.status_code == 200
    assert response.json() == {"description": "test", "id": 1}


@pytest.mark.anyio
async def test_get_random_word_404_empty_description_table_in_db(
    db_session: Session, async_client: AsyncClient
):
    expected_message = "No descriptions found in the database."
    response = await async_client.get("/shuffle/random_desc")

    assert response.status_code == 404
    assert response.json()["detail"] == expected_message

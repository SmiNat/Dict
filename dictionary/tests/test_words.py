import logging

import pytest
from fastapi import status
from fastapi.encoders import jsonable_encoder
from httpx import AsyncClient
from sqlalchemy.orm import Session

from dictionary.enums import MasterLevel
from dictionary.models import Word
from dictionary.tests.conftest import TestingSessionLocal

logger = logging.getLogger(__name__)


def create_word(
    word: str = "pivot",
    master_level: str = MasterLevel.NEW,
    notes: str = None,
):
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


def test_create_word(db_session: Session):
    word = create_word(word="pivot on sth", master_level=MasterLevel.NEW)

    assert word.word == "pivot on sth"
    assert word.master_level == MasterLevel.NEW


@pytest.mark.anyio
async def test_get_all_words_empty(async_client: AsyncClient, db_session: Session):
    expected_response = {"number_of_words": 0, "words": []}
    response = await async_client.get("/words/all")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_response


@pytest.mark.anyio
async def test_get_all_words_with_single_word_in_db(
    async_client: AsyncClient, db_session: Session
):
    word = create_word()
    expected_response = {
        "number_of_words": 1,
        "words": [
            jsonable_encoder(
                word,
                exclude_none=True,
                exclude_unset=True,
                exclude=["created", "updated"],
            )
        ],
    }
    response = await async_client.get("words/all")

    assert response.status_code == 200
    assert response.json() == expected_response


@pytest.mark.anyio
async def test_get_all_words_with_multiple_words_in_db(
    async_client: AsyncClient, db_session: Session
):
    word_1 = create_word()
    word_2 = create_word(word="test")
    word_3 = create_word(word="fallout")
    words = [word_1, word_2, word_3]
    expected_response = {
        "number_of_words": 3,
        "words": [
            jsonable_encoder(
                word,
                exclude_none=True,
                exclude_unset=True,
                exclude=["created", "updated"],
            )
            for word in words
        ],
    }
    response = await async_client.get("words/all")

    assert response.status_code == 200
    assert response.json() == expected_response

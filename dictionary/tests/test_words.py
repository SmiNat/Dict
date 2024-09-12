import logging

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.orm import Session

from dictionary.enums import MasterLevel
from dictionary.models import Word

logger = logging.getLogger(__name__)


"""⚠️ NOTE: In case of test failures, try to run tests using the commend: \
pytest --asyncio-mode=auto"""


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


def test_create_word(db_session: Session):
    word = create_word(db_session, word="pivot on sth", master_level=MasterLevel.NEW)

    assert word.word == "pivot on sth"
    assert word.master_level == MasterLevel.NEW


@pytest.mark.anyio
async def test_get_all_words_empty(async_client: AsyncClient, db_session: Session):
    expected_response = {"number_of_words": 0, "words": []}
    response = await async_client.get("/words/all")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_response


@pytest.mark.anyio
async def test_get_all_words_with_single_word(
    async_client: AsyncClient, db_session: Session
):
    create_word(db_session)
    expected_response = {
        "number_of_words": 1,
        "words": [{"word": "pivot", "master_level": "new", "id": 1}],
    }
    response = await async_client.get("words/all")

    assert response.status_code == 200
    assert response.json() == expected_response

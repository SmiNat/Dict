import logging

import pytest
from fastapi import status
from fastapi.encoders import jsonable_encoder
from httpx import AsyncClient
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from dictionary.enums import MasterLevel
from dictionary.models import Word
from dictionary.tests.utils import (
    create_description,
    create_full_dict_entry,
    create_word,
    create_word_definition_association_table,
)

logger = logging.getLogger(__name__)


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
    word_2 = create_word(word="test", notes="test note")
    word_3 = create_word(word="fallout", master_level="hard")
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

    logger.debug("Get all words response: %s" % response.json())

    assert response.status_code == 200
    assert response.json() == expected_response


@pytest.mark.anyio
async def test_get_word_translation_empty_query_params(
    async_client: AsyncClient, db_session: Session
):
    expected_response = "Either 'id' or 'search' parameter must be given."

    response = await async_client.get("/words/translations")
    assert response.status_code == 400
    assert response.json()["detail"] == expected_response


@pytest.mark.anyio
async def test_get_word_translation_no_word_id(
    async_client: AsyncClient, db_session: Session
):
    word_id = 1
    expected_response = f"No word with ID {word_id} stored in the database."

    response = await async_client.get(
        "/words/translations", params={"word_id": word_id}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == expected_response


@pytest.mark.anyio
async def test_get_word_translation_no_searched_word(
    async_client: AsyncClient, db_session: Session
):
    search = "pivot"
    expected_response = f"No word '{search}' stored in the database."

    response = await async_client.get("/words/translations", params={"search": search})
    assert response.status_code == 404
    assert response.json()["detail"] == expected_response


@pytest.mark.anyio
async def test_get_word_translation_word_id_with_no_translations(
    async_client: AsyncClient, db_session: Session
):
    word = create_word()
    expected_response = "No translations stored in the database."

    response = await async_client.get(
        "/words/translations", params={"word_id": word.id}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == expected_response


@pytest.mark.anyio
async def test_get_word_translation_word_id_with_single_translation(
    async_client: AsyncClient, db_session: Session
):
    word = create_word()
    desc = create_description()
    create_word_definition_association_table(word.id, desc.id)
    expected_response = {"word": word.word, "translation": [desc.in_polish]}

    response = await async_client.get(
        "/words/translations", params={"word_id": word.id}
    )
    assert response.status_code == 200
    assert response.json() == expected_response


@pytest.mark.anyio
async def test_get_word_translation_word_id_with_multiple_translations(
    async_client: AsyncClient, db_session: Session
):
    word, desc_1 = create_full_dict_entry()
    desc_2 = create_description(in_polish="test")
    create_word_definition_association_table(word.id, desc_2.id)
    expected_response = {
        "word": word.word,
        "translation": [desc_1.in_polish, desc_2.in_polish],
    }

    response = await async_client.get(
        "/words/translations", params={"word_id": word.id}
    )
    assert response.status_code == 200
    assert response.json() == expected_response


@pytest.mark.anyio
async def test_get_word_translation_search_single_word_with_no_translations(
    async_client: AsyncClient, db_session: Session
):
    word = create_word()
    expected_response = [
        {"word": {"word": word.word, "id": word.id}, "translation": []}
    ]

    response = await async_client.get(
        "/words/translations", params={"search": word.word}
    )
    assert response.status_code == 200
    assert response.json() == expected_response


@pytest.mark.anyio
async def test_get_word_translation_search_single_word_with_single_translation(
    async_client: AsyncClient, db_session: Session
):
    word, desc = create_full_dict_entry()
    expected_response = [
        {"word": {"word": word.word, "id": word.id}, "translation": [desc.in_polish]}
    ]

    response = await async_client.get(
        "/words/translations", params={"search": word.word}
    )
    assert response.status_code == 200
    assert response.json() == expected_response


@pytest.mark.anyio
async def test_get_word_translation_search_single_word_with_multiple_translations(
    async_client: AsyncClient, db_session: Session
):
    word_1, desc_1 = create_full_dict_entry()
    desc_2 = create_full_dict_entry(
        word_id=word_1.id, in_polish="test", example="example"
    )  # word_1, desc_2
    expected_response = [
        {
            "word": {"word": word_1.word, "id": word_1.id},
            "translation": [desc_1.in_polish, desc_2.in_polish],
        }
    ]

    response = await async_client.get(
        "/words/translations", params={"search": word_1.word}
    )
    assert response.status_code == 200
    assert response.json() == expected_response


@pytest.mark.anyio
async def test_get_word_translation_search_multiple_words_with_no_translations(
    async_client: AsyncClient, db_session: Session
):
    word = create_word(word="pivot")
    word_2 = create_word(word="pivot on sth")
    expected_response = [
        {"word": {"word": word.word, "id": word.id}, "translation": []},
        {"word": {"word": word_2.word, "id": word_2.id}, "translation": []},
    ]

    response = await async_client.get(
        "/words/translations", params={"search": word.word}
    )
    assert response.status_code == 200
    assert response.json() == expected_response


@pytest.mark.anyio
async def test_get_word_translation_search_multiple_words_with_translations(
    async_client: AsyncClient, db_session: Session
):
    word_1, desc_1 = create_full_dict_entry(word="pivot")  # word_1, desc_1
    desc_2 = create_full_dict_entry(
        word_id=word_1.id, in_polish="oś, trzpień"
    )  # word_1, desc_2
    word_2, desc_3 = create_full_dict_entry(
        word="pivot on sth", in_polish="zależeć od czegoś", type="verb"
    )  # word_2, desc_3
    word_3 = create_word(word="pivot man")
    word_4 = create_word(word="test")

    expected_response = [
        {
            "word": {"word": word_1.word, "id": word_1.id},
            "translation": [desc_1.in_polish, desc_2.in_polish],
        },
        {
            "word": {"word": word_2.word, "id": word_2.id},
            "translation": [desc_3.in_polish],
        },
        {
            "word": {"word": word_3.word, "id": word_3.id},
            "translation": [],
        },
    ]

    response = await async_client.get(
        "/words/translations", params={"search": word_1.word}
    )
    assert response.status_code == 200
    assert response.json() == expected_response


@pytest.mark.anyio
async def test_get_all_dict_data_empty_db(
    async_client: AsyncClient, db_session: Session
):
    expected_response = "Empty database."

    response = await async_client.get("/words/descriptions")
    assert response.status_code == 404
    assert response.json()["detail"] == expected_response


@pytest.mark.anyio
async def test_get_all_dict_data_single_word_no_description(
    async_client: AsyncClient, db_session: Session
):
    word = create_word()
    expected_response = [
        {
            "word": jsonable_encoder(
                word, exclude=["created", "updated"], exclude_none=True
            ),
            "description": [],
        }
    ]

    response = await async_client.get("/words/descriptions")
    assert response.status_code == 200
    assert response.json() == expected_response


@pytest.mark.anyio
async def test_get_all_dict_data_single_word_single_description(
    async_client: AsyncClient, db_session: Session
):
    word, desc = create_full_dict_entry()
    expected_response = [
        {
            "word": jsonable_encoder(
                word, exclude=["created", "updated"], exclude_none=True
            ),
            "description": [
                jsonable_encoder(
                    desc, exclude_none=True, exclude=["created", "updated"]
                )
            ],
        }
    ]

    response = await async_client.get("/words/descriptions")
    assert response.status_code == 200
    assert response.json() == expected_response


@pytest.mark.anyio
async def test_get_all_dict_data_single_word_multiple_descriptions(
    async_client: AsyncClient, db_session: Session
):
    word_1, desc_1 = create_full_dict_entry()
    desc_2 = create_full_dict_entry(
        word_id=word_1.id, in_polish="oś, trzpień", example="test"
    )  # word_1, desc_2
    expected_response = [
        {
            "word": jsonable_encoder(
                word_1, exclude=["created", "updated"], exclude_none=True
            ),
            "description": [
                jsonable_encoder(
                    desc_1, exclude_none=True, exclude=["created", "updated"]
                ),
                jsonable_encoder(
                    desc_2, exclude_none=True, exclude=["created", "updated"]
                ),
            ],
        }
    ]

    response = await async_client.get("/words/descriptions")
    assert response.status_code == 200
    assert response.json() == expected_response


@pytest.mark.anyio
async def test_get_all_dict_data_multiple_words_multiple_descriptions(
    async_client: AsyncClient, db_session: Session
):
    word_1, desc_1 = create_full_dict_entry()
    desc_2 = create_full_dict_entry(
        word_id=word_1.id, in_polish="oś, trzpień", example="test"
    )
    desc_3 = create_full_dict_entry(word_id=word_1.id, in_polish="test")
    word_2, desc_4 = create_full_dict_entry(word="riot", in_polish="zamieszki")
    create_word_definition_association_table(word_2.id, desc_3.id)
    expected_response = [
        {
            "word": jsonable_encoder(
                word_1, exclude=["created", "updated"], exclude_none=True
            ),
            "description": [
                jsonable_encoder(
                    desc_1, exclude_none=True, exclude=["created", "updated"]
                ),
                jsonable_encoder(
                    desc_2, exclude_none=True, exclude=["created", "updated"]
                ),
                jsonable_encoder(
                    desc_3, exclude_none=True, exclude=["created", "updated"]
                ),
            ],
        },
        {
            "word": jsonable_encoder(
                word_2, exclude=["created", "updated"], exclude_none=True
            ),
            "description": [
                jsonable_encoder(
                    desc_3, exclude_none=True, exclude=["created", "updated"]
                ),
                jsonable_encoder(
                    desc_4, exclude_none=True, exclude=["created", "updated"]
                ),
            ],
        },
    ]

    response = await async_client.get("/words/descriptions")
    assert response.status_code == 200
    assert response.json() == expected_response


@pytest.mark.anyio
async def test_get_single_word_empty_db(async_client: AsyncClient, db_session: Session):
    word_id = 1
    expected_response = f"No word with the ID {word_id} stored in the database."

    response = await async_client.get(f"/words/single/{word_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == expected_response


@pytest.mark.anyio
async def test_get_single_word_with_no_description(
    async_client: AsyncClient, db_session: Session
):
    word = create_word(notes="test")
    expected_response = {
        "word": jsonable_encoder(
            word, exclude=["created", "updated"], exclude_none=True
        ),
        "description": [],
    }

    response = await async_client.get(f"/words/single/{word.id}")
    assert response.status_code == 200
    assert response.json() == expected_response


@pytest.mark.anyio
async def test_get_single_word_with_with_single_description(
    async_client: AsyncClient, db_session: Session
):
    word, desc = create_full_dict_entry(notes="test")
    expected_response = {
        "word": jsonable_encoder(
            word, exclude=["created", "updated"], exclude_none=True
        ),
        "description": [
            jsonable_encoder(desc, exclude_none=True, exclude=["created", "updated"])
        ],
    }

    response = await async_client.get(f"/words/single/{word.id}")
    assert response.status_code == 200
    assert response.json() == expected_response


@pytest.mark.anyio
async def test_get_single_word_with_with_multiple_descriptions(
    async_client: AsyncClient, db_session: Session
):
    word, desc_1 = create_full_dict_entry(notes="test")
    desc_2 = create_full_dict_entry(
        word_id=word.id, in_polish="oś, dźwignia", example="test"
    )
    expected_response = {
        "word": jsonable_encoder(
            word, exclude=["created", "updated"], exclude_none=True
        ),
        "description": [
            jsonable_encoder(desc_1, exclude_none=True, exclude=["created", "updated"]),
            jsonable_encoder(desc_2, exclude_none=True, exclude=["created", "updated"]),
        ],
    }

    response = await async_client.get(f"/words/single/{word.id}")
    assert response.status_code == 200
    assert response.json() == expected_response


@pytest.mark.anyio
async def test_add_new_word_successfull(async_client: AsyncClient, db_session: Session):
    payload = {"word": "test", "master_level": MasterLevel.NEW, "notes": "example"}
    word = db_session.query(Word).filter_by(word=payload["word"]).first()
    assert word is None

    response = await async_client.post("/words/add", json=payload)
    word = db_session.query(Word).filter_by(word=payload["word"]).first()
    expected_response = jsonable_encoder(
        word, exclude_none=True, exclude=["created", "updated"]
    )

    assert response.status_code == 201
    assert response.json() == expected_response


@pytest.mark.anyio
async def test_add_new_word_intgrity_error_while_adding_the_same_word(
    async_client: AsyncClient, db_session: Session
):
    word = create_word(word="test")
    word = db_session.query(Word).filter_by(word=word.word).first()
    assert word is not None

    payload = {"word": word.word, "master_level": MasterLevel.HARD, "notes": "example"}

    try:
        response = await async_client.post("/words/add", json=payload)
    except IntegrityError as exc_info:
        db_session.rollback()  # Rollback the session to reset its state
        expected_message = (
            'duplicate key value violates unique constraint "word_word_key"'
        )
        assert expected_message in str(exc_info.orig)
        added_word = db_session.query(Word).filter_by(word=payload["word"]).first()
        assert added_word is None

    expected_response = "Unique constraint violated. Key (word)=(test) already exists."
    assert response.status_code == 400
    assert response.json()["detail"] == expected_response


@pytest.mark.anyio
async def test_add_new_word_invalid_enum_parameter(
    async_client: AsyncClient, db_session: Session
):
    payload = {"word": "test", "master_level": "invalid", "notes": "example"}
    expected_response = "Input should be 'new', 'medium', 'prefect' or 'hard'"

    response = await async_client.post("/words/add", json=payload)

    assert response.status_code == 422
    assert expected_response in response.json()["detail"][0]["msg"]
    added_word = db_session.query(Word).filter_by(word=payload["word"]).first()
    assert added_word is None


@pytest.mark.anyio
async def test_update_a_word_with_word_not_found(
    async_client: AsyncClient, db_session: Session
):
    word_id = 1
    payload = {"word": "test", "master_level": MasterLevel.NEW, "notes": "example"}
    expected_response = f"Word with ID: {word_id} was not found."

    response = await async_client.patch(f"/words/update/{word_id}", json=payload)
    assert response.status_code == 404
    assert response.json()["detail"] == expected_response


@pytest.mark.anyio
async def test_update_a_word_successfully(
    async_client: AsyncClient, db_session: Session
):
    word = create_word()
    word = db_session.query(Word).filter_by(word=word.word).first()
    assert word is not None
    assert word.created == word.updated

    payload = {"word": "test", "master_level": MasterLevel.NEW, "notes": "example"}

    response = await async_client.patch(f"/words/update/{word.id}", json=payload)
    word_updated = db_session.query(Word).filter_by(word=payload["word"]).first()
    assert word_updated is not None
    assert word.id == word_updated.id
    assert response.status_code == 200
    assert response.json() == jsonable_encoder(
        word_updated, exclude_none=True, exclude=["created", "updated"]
    )
    assert word_updated.created == word.created
    assert word_updated.created != word_updated.updated


@pytest.mark.anyio
async def test_update_a_word_integrity_error(
    async_client: AsyncClient, db_session: Session
):
    word = create_word()
    word_2 = create_word(word="test")

    payload = {"word": "test", "master_level": MasterLevel.NEW, "notes": "example"}

    try:
        response = await async_client.patch(f"/words/update/{word.id}", json=payload)
    except IntegrityError as exc_info:
        db_session.rollback()  # Rollback the session to reset its state
        expected_message = (
            'duplicate key value violates unique constraint "word_word_key"'
        )
        assert expected_message in str(exc_info.orig)
        updated_word = db_session.query(Word).filter_by(id=word.id).first()
        assert updated_word.word == word.word

    expected_response = "Unique constraint violated. Key (word)=(test) already exists."
    assert response.status_code == 400
    assert response.json()["detail"] == expected_response


@pytest.mark.anyio
async def test_update_a_word_invalid_enum_parameter(
    async_client: AsyncClient, db_session: Session
):
    word = create_word()
    payload = {"master_level": "invalid"}
    expected_response = "Input should be 'new', 'medium', 'prefect' or 'hard'"

    response = await async_client.patch(f"/words/update/{word.id}", json=payload)

    assert response.status_code == 422
    assert expected_response in response.json()["detail"][0]["msg"]
    word_updated = db_session.query(Word).filter_by(id=word.id).first()
    assert word_updated.master_level != "invalid"
    assert word_updated.master_level == "new"


@pytest.mark.anyio
async def test_delete_a_word_successfully(
    async_client: AsyncClient, db_session: Session
):
    word = create_word()
    word = db_session.query(Word).filter_by(word=word.word).first()
    assert word is not None

    response = await async_client.delete(f"/words/delete/{word.id}")

    assert response.status_code == 204
    word = db_session.query(Word).filter_by(word=word.word).first()
    assert word is None


@pytest.mark.anyio
async def test_delete_a_word_invalid_word_id(
    async_client: AsyncClient, db_session: Session
):
    word_id = 1
    expected_response = f"Word with the ID: {word_id} was not found."

    response = await async_client.delete(f"/words/delete/{word_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == expected_response

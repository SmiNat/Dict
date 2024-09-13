import logging

import pytest
from fastapi import status
from fastapi.encoders import jsonable_encoder
from httpx import AsyncClient
from sqlalchemy.orm import Session

from dictionary.enums import MasterLevel
from dictionary.tests.utils import (
    create_description,
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
    word = create_word()
    desc_1 = create_description()
    desc_2 = create_description(in_polish="test")
    create_word_definition_association_table(word.id, desc_1.id)
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
    word = create_word()
    desc = create_description()
    create_word_definition_association_table(word.id, desc.id)
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
    word = create_word()
    desc_1 = create_description()
    desc_2 = create_description(in_polish="test", example="example")
    create_word_definition_association_table(word.id, desc_1.id)
    create_word_definition_association_table(word.id, desc_2.id)
    expected_response = [
        {
            "word": {"word": word.word, "id": word.id},
            "translation": [desc_1.in_polish, desc_2.in_polish],
        }
    ]

    response = await async_client.get(
        "/words/translations", params={"search": word.word}
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
    word = create_word(word="pivot")
    word_2 = create_word(word="pivot on sth")
    word_3 = create_word(word="pivot man")
    word_4 = create_word(word="test")
    desc = create_description()
    desc_2 = create_description(in_polish="oś, trzpień")
    desc_22 = create_description(in_polish="zależeć od czegoś", type="verb")
    create_word_definition_association_table(word.id, desc.id)
    create_word_definition_association_table(word.id, desc_2.id)
    create_word_definition_association_table(word_2.id, desc_22.id)
    expected_response = [
        {
            "word": {"word": word.word, "id": word.id},
            "translation": [desc.in_polish, desc_2.in_polish],
        },
        {
            "word": {"word": word_2.word, "id": word_2.id},
            "translation": [desc_22.in_polish],
        },
        {
            "word": {"word": word_3.word, "id": word_3.id},
            "translation": [],
        },
    ]

    response = await async_client.get(
        "/words/translations", params={"search": word.word}
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
    word = create_word()
    desc = create_description()
    create_word_definition_association_table(word.id, desc.id)
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
    word = create_word()
    desc_1 = create_description()
    desc_2 = create_description(in_polish="oś, trzpień", example="test")
    create_word_definition_association_table(word.id, desc_1.id)
    create_word_definition_association_table(word.id, desc_2.id)
    expected_response = [
        {
            "word": jsonable_encoder(
                word, exclude=["created", "updated"], exclude_none=True
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
    word_1 = create_word()
    word_2 = create_word(word="riot")
    desc_1 = create_description()
    desc_2 = create_description(in_polish="oś, trzpień", example="test")
    desc_3 = create_description(in_polish="zamieszki")
    desc_4 = create_description(in_polish="test")  # associated with both words
    create_word_definition_association_table(word_1.id, desc_1.id)
    create_word_definition_association_table(word_1.id, desc_2.id)
    create_word_definition_association_table(word_1.id, desc_4.id)
    create_word_definition_association_table(word_2.id, desc_3.id)
    create_word_definition_association_table(word_2.id, desc_4.id)
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
                    desc_4, exclude_none=True, exclude=["created", "updated"]
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
    word = create_word(notes="test")
    desc = create_description()
    create_word_definition_association_table(word.id, desc.id)
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
    word = create_word(notes="test")
    desc_1 = create_description()
    desc_2 = create_description(in_polish="oś, dźwignia", example="test")
    create_word_definition_association_table(word.id, desc_1.id)
    create_word_definition_association_table(word.id, desc_2.id)
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

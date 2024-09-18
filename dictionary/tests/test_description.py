import logging

import pytest
from fastapi.encoders import jsonable_encoder
from httpx import AsyncClient
from sqlalchemy.orm import Session

from dictionary.enums import WordTypes
from dictionary.models import Description, WordDescription
from dictionary.tests.utils import (
    create_description,
    create_word,
    create_word_definition_association_table,
)

logger = logging.getLogger(__name__)


def test_create_description(db_session: Session):
    desc = create_description(
        type=WordTypes.NOUN,
        in_polish="test",
        in_english="test abc",
        example="test example",
    )

    assert desc.type == WordTypes.NOUN
    assert desc.in_polish == "test"
    assert desc.in_english == "test abc"
    assert desc.example == "test example"


@pytest.mark.anyio
async def test_get_all_descriptions_empty_db(
    async_client: AsyncClient, db_session: Session
):
    expected_response = "No descriptions stored in the database."

    response = await async_client.get("/descriptions/all")
    assert response.status_code == 404
    assert response.json()["detail"] == expected_response


@pytest.mark.anyio
async def test_get_all_descriptions_with_single_desc_in_db(
    async_client: AsyncClient, db_session: Session
):
    desc = create_description()
    expected_response = {
        "number_of_descriptions": 1,
        "descriptions": [
            jsonable_encoder(desc, exclude_none=True, exclude=["created", "updated"])
        ],
    }

    response = await async_client.get("/descriptions/all")
    assert response.status_code == 200
    assert response.json() == expected_response


@pytest.mark.anyio
async def test_get_all_descriptions_with_multiple_desc_in_db(
    async_client: AsyncClient, db_session: Session
):
    desc = create_description()
    desc_2 = create_description(in_polish="test", example="test example")
    desc_3 = create_description(in_polish="pracować", type=WordTypes.VERB)
    expected_response = {
        "number_of_descriptions": 3,
        "descriptions": [
            jsonable_encoder(desc, exclude_none=True, exclude=["created", "updated"]),
            jsonable_encoder(desc_2, exclude_none=True, exclude=["created", "updated"]),
            jsonable_encoder(desc_3, exclude_none=True, exclude=["created", "updated"]),
        ],
    }

    response = await async_client.get("/descriptions/all")
    assert response.status_code == 200
    assert response.json() == expected_response


@pytest.mark.anyio
async def test_get_single_description_empty_db(
    async_client: AsyncClient, db_session: Session
):
    desc_id = 1
    expected_response = "No desctiption stored in the database."

    response = await async_client.get(f"/descriptions/single/{desc_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == expected_response


@pytest.mark.anyio
async def test_get_single_description_successful(
    async_client: AsyncClient, db_session: Session
):
    desc = create_description()
    expected_response = jsonable_encoder(
        desc, exclude_none=True, exclude=["created", "updated"]
    )

    response = await async_client.get(f"/descriptions/single/{desc.id}")
    assert response.status_code == 200
    assert response.json() == expected_response


@pytest.mark.anyio
async def test_add_new_description_successful(
    async_client: AsyncClient, db_session: Session
):
    word = create_word()
    payload = {
        "type": WordTypes.NOUN,
        "in_polish": "sedno",
        "in_english": "the point of the story",
        "example": "test",
    }
    word_desc_association_table = db_session.query(WordDescription).all()
    assert len(word_desc_association_table) == 0

    response = await async_client.post(f"/descriptions/add/{word.id}", json=payload)
    assert response.status_code == 201
    desc = (
        db_session.query(Description).filter_by(in_polish=payload["in_polish"]).first()
    )
    assert desc is not None
    expected_response = {
        "word": jsonable_encoder(word, exclude=["created", "updated"]),
        "description": [jsonable_encoder(desc, exclude=["created", "updated"])],
    }
    assert response.json() == expected_response

    word_desc_association_table = db_session.query(WordDescription).all()
    assert len(word_desc_association_table) == 1


@pytest.mark.anyio
async def test_add_new_description_invalid_word_id(
    async_client: AsyncClient, db_session: Session
):
    word_id = 1
    payload = {
        "type": WordTypes.NOUN,
        "in_polish": "sedno",
        "in_english": "the point of the story",
        "example": "test",
    }
    expected_response = "Word not found."
    word_desc_association_table = db_session.query(WordDescription).all()
    assert len(word_desc_association_table) == 0

    response = await async_client.post(f"/descriptions/add/{word_id}", json=payload)
    assert response.status_code == 404
    assert response.json()["detail"] == expected_response
    desc = (
        db_session.query(Description).filter_by(in_polish=payload["in_polish"]).first()
    )
    assert desc is None
    word_desc_association_table = db_session.query(WordDescription).all()
    assert len(word_desc_association_table) == 0


@pytest.mark.parametrize(
    "key, invalid_value, status_code, exp_response",
    [
        ("type", "invalid", 422, "Input should be 'noun', 'verb', "),
        ("in_polish", None, 422, "Input should be a valid string"),
        ("in_english", 123, 422, "Input should be a valid string"),
        ("example", 123, 422, "Input should be a valid string"),
    ],
)
@pytest.mark.anyio
async def test_add_new_description_invalid_payload(
    async_client: AsyncClient,
    db_session: Session,
    key: str,
    invalid_value: str | None,
    status_code: int,
    exp_response: str,
):
    word = create_word()
    payload = {
        "type": WordTypes.NOUN,
        "in_polish": "sedno",
        "in_english": "the point of the story",
        "example": "test",
    }

    payload[key] = invalid_value

    response = await async_client.post(f"/descriptions/add/{word.id}", json=payload)
    assert response.status_code == status_code
    assert exp_response in response.json()["detail"][0]["msg"]
    desc = (
        db_session.query(Description).filter_by(in_polish=payload["in_polish"]).first()
    )
    assert desc is None
    word_desc_association_table = db_session.query(WordDescription).all()
    assert len(word_desc_association_table) == 0


@pytest.mark.anyio
async def test_add_new_description_intgrity_error_while_adding_the_same_desc(
    async_client: AsyncClient, db_session: Session
):
    word = create_word()
    desc = create_description(in_polish="test")
    payload = {"in_polish": desc.in_polish}

    response = await async_client.post(f"/descriptions/add/{word.id}", json=payload)

    expected_response = (
        "Database constraint violated. Key (in_polish)=(test) already exists."
    )
    assert response.status_code == 400
    assert response.json()["detail"] == expected_response


@pytest.mark.anyio
async def test_assign_description_to_a_word_successful(
    async_client: AsyncClient, db_session: Session
):
    word = create_word()
    desc = create_description()
    word_desc_association_table = db_session.query(WordDescription).all()
    assert len(word_desc_association_table) == 0
    expected_response = {
        "word": jsonable_encoder(word, exclude=["created", "updated"]),
        "description": [jsonable_encoder(desc, exclude=["created", "updated"])],
    }

    response = await async_client.post(f"/descriptions/assign/{word.id}/{desc.id}")

    assert response.status_code == 201
    assert response.json() == expected_response
    word_desc_association_table = db_session.query(WordDescription).all()
    assert len(word_desc_association_table) == 1


@pytest.mark.anyio
async def test_assign_description_to_a_word_invalid_word_id(
    async_client: AsyncClient, db_session: Session
):
    word_id = 1
    desc = create_description()
    word_desc_association_table = db_session.query(WordDescription).all()
    assert len(word_desc_association_table) == 0
    expected_response = f"Word with ID: {word_id} was not found."

    response = await async_client.post(f"/descriptions/assign/{word_id}/{desc.id}")

    assert response.status_code == 404
    assert response.json()["detail"] == expected_response
    word_desc_association_table = db_session.query(WordDescription).all()
    assert len(word_desc_association_table) == 0


@pytest.mark.anyio
async def test_assign_description_to_a_word_invalid_description_id(
    async_client: AsyncClient, db_session: Session
):
    word = create_word()
    desc_id = 1
    word_desc_association_table = db_session.query(WordDescription).all()
    assert len(word_desc_association_table) == 0
    expected_response = f"Description with ID: {desc_id} was not found."

    response = await async_client.post(f"/descriptions/assign/{word.id}/{desc_id}")

    assert response.status_code == 404
    assert response.json()["detail"] == expected_response
    word_desc_association_table = db_session.query(WordDescription).all()
    assert len(word_desc_association_table) == 0


@pytest.mark.anyio
async def test_assign_description_to_a_word_invalid_word_and_description_id(
    async_client: AsyncClient, db_session: Session
):
    word_id = 1
    desc_id = 1
    word_desc_association_table = db_session.query(WordDescription).all()
    assert len(word_desc_association_table) == 0
    expected_response = f"Word with ID: {word_id} was not found."

    response = await async_client.post(f"/descriptions/assign/{word_id}/{desc_id}")

    assert response.status_code == 404
    assert response.json()["detail"] == expected_response
    word_desc_association_table = db_session.query(WordDescription).all()
    assert len(word_desc_association_table) == 0


@pytest.mark.anyio
async def test_assign_description_intgrity_error_while_adding_the_same_word_and_desc(
    async_client: AsyncClient, db_session: Session
):
    word = create_word()
    desc = create_description()
    word_desc = create_word_definition_association_table(word.id, desc.id)
    expected_response = "Database constraint violated. Key (word_id, description_id)=(1, 1) already exists."

    response = await async_client.post(f"/descriptions/assign/{word.id}/{desc.id}")

    assert response.status_code == 400
    assert response.json()["detail"] == expected_response


@pytest.mark.anyio
async def test_update_description_successful(
    async_client: AsyncClient, db_session: Session
):
    desc = create_description()
    payload = {
        "type": WordTypes.ADJECTIVE,
        "in_polish": "nowy opis",
        "in_english": "new desc",
        "example": "new example",
    }

    response = await async_client.patch(f"/descriptions/update/{desc.id}", json=payload)

    assert response.status_code == 200
    new_desc = db_session.query(Description).filter_by(id=desc.id).first()
    expected_response = jsonable_encoder(
        new_desc, exclude_none=True, exclude_unset=True, exclude=["created", "updated"]
    )
    assert response.json() == expected_response
    assert desc.created == new_desc.created
    assert desc.updated != new_desc.updated


@pytest.mark.parametrize(
    "key, invalid_value, code, exp_response",
    [
        ("type", "invalid", 422, "Input should be 'noun', 'verb'"),
        ("in_english", 123, 422, "Input should be a valid string"),
        ("example", {"invalid": "invalid"}, 422, "Input should be a valid string"),
    ],
)
@pytest.mark.anyio
async def test_update_description_invalid_payload(
    async_client: AsyncClient,
    db_session: Session,
    key: str,
    invalid_value: str | None,
    code: int,
    exp_response: str,
):
    desc = create_description()
    payload = {
        "type": WordTypes.ADJECTIVE,
        "in_polish": "nowy opis",
        "in_english": "new desc",
        "example": "new example",
    }
    payload[key] = invalid_value

    response = await async_client.patch(f"/descriptions/update/{desc.id}", json=payload)

    assert response.status_code == code
    assert exp_response in response.json()["detail"][0]["msg"]


@pytest.mark.anyio
async def test_update_description_invalid_description_id(
    async_client: AsyncClient, db_session: Session
):
    desc = create_description()
    payload = {
        "type": WordTypes.ADJECTIVE,
        "in_polish": "nowy opis",
        "in_english": "new desc",
        "example": "new example",
    }
    desc_id = 111
    expected_response = f"Description with ID: {desc_id} was not found."

    response = await async_client.patch(f"/descriptions/update/{desc_id}", json=payload)

    assert response.status_code == 404
    assert response.json()["detail"] == expected_response


@pytest.mark.anyio
async def test_update_description_integrity_error(
    async_client: AsyncClient, db_session: Session
):
    desc = create_description()
    desc_2 = create_description(in_polish="test")
    payload = {"type": WordTypes.ADJECTIVE, "in_polish": desc_2.in_polish}
    expected_response = (
        "Database constraint violated. Key (in_polish)=(test) already exists."
    )

    response = await async_client.patch(f"/descriptions/update/{desc.id}", json=payload)

    assert response.status_code == 400
    assert response.json()["detail"] == expected_response


@pytest.mark.anyio
async def test_delete_description_successfully(
    async_client: AsyncClient, db_session: Session
):
    desc = create_description()
    desc = db_session.query(Description).filter_by(id=desc.id).first()
    assert desc is not None

    response = await async_client.delete(f"/descriptions/delete/{desc.id}")

    assert response.status_code == 204
    desc = db_session.query(Description).filter_by(id=desc.id).first()
    assert desc is None


@pytest.mark.anyio
async def test_delete_description_invalid_description_id(
    async_client: AsyncClient, db_session: Session
):
    desc_id = 123
    expected_response = f"Description with the ID: {desc_id} was not found."

    response = await async_client.delete(f"/descriptions/delete/{desc_id}")

    assert response.status_code == 404
    assert response.json()["detail"] == expected_response

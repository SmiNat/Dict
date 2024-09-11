import datetime
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .database import get_db
from .models import Description, Word, WordDescription
from .schemas import (
    AllDescriptions,
    AllWords,
    DescriptionModel,
    DescriptionReturn,
    DescriptionUpdate,
    WordDescriptionsModel,
    WordModel,
    WordReturn,
    WordUpdate,
)
from .utils import integrity_error_handler

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/dict", tags=["dict"])


db_dependency = Annotated[Session, Depends(get_db)]


@router.get(
    "/words",
    response_model=AllWords,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
    status_code=200,
    description="Fetch all the data from the Words table.",
)
async def get_all_words(db: db_dependency):
    query = db.query(Word)

    if not query:
        raise HTTPException(404, "No words stored in the database.")

    return {"number_of_words": query.count(), "words": query.all()}


@router.get(
    "/word/translations",
    response_model=None,
    status_code=200,
    description="Search for word translations by word ID or the word itself.",
)
async def get_word_translations(
    db: db_dependency, word_id: int | None = None, search: str | None = None
):
    if not word_id and not search:
        raise HTTPException(400, "Either 'id' or 'search' parameter must be given.")

    # If user searches using word_id parameter
    if word_id:
        word = db.query(Word).filter_by(id=word_id).first()

        if not word:
            raise HTTPException(
                404, f"No word with ID {word_id} stored in the database."
            )

        translations = (
            db.query(Description.in_polish)
            .join(WordDescription, WordDescription.description_id == Description.id)
            .filter(WordDescription.word_id == word_id)
            .all()
        )
        if not translations:
            raise HTTPException(404, "No descriptions stored in the database.")

        translation_list = [translation[0] for translation in translations]

        return {"word": word.word, "translation": translation_list}

    # If user searches using search parameter
    words = db.query(Word).filter(Word.word.icontains(search)).all()
    if not words:
        raise HTTPException(404, f"No word '{search}' stored in the database.")

    results = []
    for record in words:
        translations = (
            db.query(Description.in_polish)
            .join(WordDescription, WordDescription.description_id == Description.id)
            .filter(WordDescription.word_id == record.id)
            .all()
        )

        translation_list = [translation[0] for translation in translations]
        results.append(
            {
                "word": {"word": record.word, "id": record.id},
                "translation": translation_list,
            }
        )

    return results


@router.get(
    "/word/{word_id}",
    response_model=WordDescriptionsModel,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
    status_code=200,
    description="Get full information about the word by its ID.",
)
async def get_single_word(db: db_dependency, word_id: int):
    word = db.query(Word).filter_by(id=word_id).first()

    if not word:
        raise HTTPException(
            404, f"No word with the ID {word_id} is stored in the database."
        )

    desc = (
        db.query(Description)
        .join(WordDescription, WordDescription.description_id == Description.id)
        .filter(WordDescription.word_id == word_id)
        .all()
    )

    return {"word": word, "description": desc}


@router.get(
    "/descriptions",
    response_model=AllDescriptions,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
    status_code=200,
    description="Fetch all the data from the Words table.",
)
async def get_all_descriptions(db: db_dependency):
    query = db.query(Description)

    if not query:
        raise HTTPException(404, "No descriptions stored in the database.")

    return {"number_of_descriptions": query.count(), "descriptions": query.all()}


@router.get(
    "/description/{desc_id}",
    response_model=DescriptionReturn,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
    status_code=200,
)
async def get_single_description(db: db_dependency, desc_id: int):
    desc = db.query(Description).filter_by(id=desc_id).first()

    if not desc:
        raise HTTPException(404, "No desctiption stored in the database.")

    return desc


@router.get(
    "/all",
    status_code=200,
    response_model=list[WordDescriptionsModel],
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
)
async def get_all_dict_data(db: db_dependency):
    words = db.query(Word).all()
    if not words:
        raise HTTPException(404, "Empty database.")

    result = []
    for word in words:
        descriptions = (
            db.query(Description)
            .join(WordDescription, WordDescription.description_id == Description.id)
            .filter(WordDescription.word_id == word.id)
            .all()
        )

        # Converting SQLAlchemy objects to Pydantic models
        word_data = WordReturn.model_validate(word)
        description_data = [
            DescriptionReturn.model_validate(desc) for desc in descriptions
        ]

        result.append({"word": word_data, "description": description_data})

    return result


@router.post("/word/add", response_model=WordReturn, status_code=201)
async def add_a_new_word(db: db_dependency, new_word: WordModel):
    model = new_word.model_dump()
    word = Word(**model)

    try:
        db.add(word)
        db.commit()

    except IntegrityError as exc:
        integrity_error_handler(exc)

    return word


@router.post(
    "/description/add/{word_id}", response_model=WordDescriptionsModel, status_code=201
)
async def add_a_new_description(
    db: db_dependency, word_id: int, new_desc: DescriptionModel
):
    word = db.query(Word).filter_by(id=word_id).first()
    if not word:
        raise HTTPException(404, "Word not found.")

    try:
        desc = Description(**new_desc.model_dump())
        db.add(desc)
        db.commit()

        association_table = WordDescription(word_id=word_id, description_id=desc.id)
        db.add(association_table)
        db.commit()

        desc = (
            db.query(Description)
            .join(WordDescription, WordDescription.description_id == Description.id)
            .filter(WordDescription.word_id == word_id)
            .all()
        )

    except IntegrityError as exc:
        integrity_error_handler(exc)

    return {"word": {"word": word.word, "id": word.id}, "description": desc}


@router.post(
    "/description/assign/{word_id}/{desc_id}",
    response_model=WordDescriptionsModel,
    status_code=201,
    description="Assign an existing description to the existing word.",
)
async def assign_description_to_a_word(db: db_dependency, word_id: int, desc_id: int):
    word = db.query(Word).filter_by(id=word_id).first()
    if not word:
        raise HTTPException(404, f"Word with the ID of {word_id} was not found.")

    desc = db.query(Description).filter_by(id=desc_id).first()
    if not desc:
        raise HTTPException(404, f"Description with the ID of {desc_id} was not found.")

    association_table = WordDescription(word_id=word_id, description_id=desc_id)

    try:
        db.add(association_table)
        db.commit()

        desc = (
            db.query(Description)
            .join(WordDescription, WordDescription.description_id == Description.id)
            .filter(WordDescription.word_id == word_id)
            .all()
        )

    except IntegrityError as exc:
        integrity_error_handler(exc)

    return {"word": {"word": word.word, "id": word.id}, "description": desc}


@router.patch(
    "/word/update/{word_id}",
    status_code=200,
    response_model=WordReturn,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
    description="**NOTE**: Delete fields you don't wish to change them - leaving field \
        with 'null' value will remove field content.",
)
async def update_word(db: db_dependency, word_id: int, update: WordUpdate):
    word = db.query(Word).filter_by(id=word_id).first()
    if not word:
        raise HTTPException(404, f"Word with the ID: {word_id} was not found.")

    fields_to_update = update.model_dump(exclude_unset=True)
    for field, value in fields_to_update.items():
        setattr(word, field, value)
    word.updated = datetime.datetime.now()

    try:
        db.commit()
        db.refresh(word)

    except IntegrityError as exc:
        integrity_error_handler(exc)

    logger.debug("Word '%s' (id: %s) was successfully updated." % (word.word, word.id))

    return word


@router.patch(
    "/description/update/{desc_id}",
    status_code=200,
    response_model=DescriptionReturn,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
    description="**NOTE**: Delete fields you don't wish to change them - leaving field \
        with 'null' value will remove field content.",
)
async def update_description(
    db: db_dependency, desc_id: int, update: DescriptionUpdate
):
    description = db.query(Description).filter_by(id=desc_id).first()
    if not description:
        raise HTTPException(404, f"Description with the ID: {desc_id} was not found.")

    fields_to_update = update.model_dump(exclude_unset=True)
    for field, value in fields_to_update.items():
        setattr(description, field, value)
    description.updated = datetime.datetime.now()

    try:
        db.commit()
        db.refresh(description)

    except IntegrityError as exc:
        integrity_error_handler(exc)

    logger.debug("Description with id: %s was successfully updated." % (description.id))

    return description


@router.delete("/word/delete/{word_id}", status_code=204)
async def delete_a_word(db: db_dependency, word_id: int):
    word = db.query(Word).filter_by(id=word_id).first()
    if not word:
        raise HTTPException(404, f"Word with the ID: {word_id} was not found.")

    db.delete(word)
    db.commit()

    logger.debug("Word '%s' (id: %s) was successfully deleted." % (word.word, word.id))


@router.delete("/word/description/{desc_id}", status_code=204)
async def delete_a_description(db: db_dependency, desc_id: int):
    description = db.query(Description).filter_by(id=desc_id).first()
    if not description:
        raise HTTPException(404, f"Description with the ID: {desc_id} was not found.")

    db.delete(description)
    db.commit()

    logger.debug("Description with id: %s was successfully deleted." % (description.id))

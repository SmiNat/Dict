import datetime
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from dictionary.database import get_db
from dictionary.models import Description, Word, WordDescription
from dictionary.schemas import (
    AllWords,
    DescriptionReturn,
    WordDescriptionsModel,
    WordModel,
    WordReturn,
    WordUpdate,
)
from dictionary.utils import integrity_error_handler

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/words", tags=["words"])


db_dependency = Annotated[Session, Depends(get_db)]


@router.get(
    "/descriptions",
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


@router.get(
    "/all",
    response_model=AllWords,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
    status_code=200,
    description="Fetch all the data from the Words table.",
)
async def get_all_words(db: db_dependency):
    query = db.query(Word)

    return {"number_of_words": query.count(), "words": query.all()}


@router.get(
    "/translations",
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
            raise HTTPException(404, "No translations stored in the database.")

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
    "/single/{word_id}",
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
            404, f"No word with the ID {word_id} stored in the database."
        )

    desc = (
        db.query(Description)
        .join(WordDescription, WordDescription.description_id == Description.id)
        .filter(WordDescription.word_id == word_id)
        .all()
    )

    return {"word": word, "description": desc}


@router.post("/add", response_model=WordReturn, status_code=201)
async def add_a_new_word(db: db_dependency, new_word: WordModel):
    model = new_word.model_dump()
    word = Word(**model)

    try:
        db.add(word)
        db.commit()

    except IntegrityError as exc:
        integrity_error_handler(exc)

    logger.debug("Word '%s' (id: %s) was successfully created." % (word.word, word.id))

    return word


@router.patch(
    "/update/{word_id}",
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
        raise HTTPException(404, f"Word with ID: {word_id} was not found.")
    sentence = word.word

    fields_to_update = update.model_dump(exclude_unset=True)
    for field, value in fields_to_update.items():
        setattr(word, field, value)
    word.updated = datetime.datetime.now()

    try:
        db.commit()
        db.refresh(word)

    except IntegrityError as exc:
        integrity_error_handler(exc)

    logger.debug(
        "Word '%s' (id: %s) was successfully updated to '%s'."
        % (sentence, word.id, word.word)
    )

    return word


@router.delete("/delete/{word_id}", status_code=204)
async def delete_a_word(db: db_dependency, word_id: int):
    word = db.query(Word).filter_by(id=word_id).first()
    if not word:
        raise HTTPException(404, f"Word with the ID: {word_id} was not found.")

    db.delete(word)
    db.commit()

    logger.debug("Word '%s' (id: %s) was successfully deleted." % (word.word, word.id))

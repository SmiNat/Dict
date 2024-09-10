import logging
from typing import Annotated, NoReturn

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
    WordDescriptionsModel,
    WordModel,
    WordReturn,
)

logging.basicConfig(
    level=logging.DEBUG,
    format="\033[94m%(levelname)-9s %(name)s | %(filename)s | %(lineno)s\033[0m --- [%(message)s]",
    handlers=[logging.FileHandler("debug.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


router = APIRouter(prefix="/dict", tags=["dict"])


db_dependency = Annotated[Session, Depends(get_db)]


def integrity_error_handler(exc_info: IntegrityError) -> NoReturn:
    logger.debug(
        f"⚠️  Unique constraint violated. ERROR: {str(exc_info.orig).strip("\n").replace("\n", ". ")}"
    )
    message = str(exc_info.orig)[str(exc_info.orig).find("DETAIL:") + 8 :].strip()
    raise HTTPException(400, f"Unique constraint violated. {message}")


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


@router.post("/new_word", response_model=WordReturn, status_code=201)
async def add_a_new_word(db: db_dependency, new_word: WordModel):
    model = new_word.model_dump()
    word = Word(**model)

    try:
        db.add(word)
        db.commit()

        return word

    except IntegrityError as exc:
        integrity_error_handler(exc)


@router.post(
    "/new_description/{word_id}", response_model=WordDescriptionsModel, status_code=201
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

        return {"word": {"word": word.word, "id": word.id}, "description": desc}

    except IntegrityError as exc:
        integrity_error_handler(exc)


@router.post(
    "/assign_description/{word_id}/{desc_id}",
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

        return {"word": {"word": word.word, "id": word.id}, "description": desc}

    except IntegrityError as exc:
        integrity_error_handler(exc)

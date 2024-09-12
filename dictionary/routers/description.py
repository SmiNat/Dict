import datetime
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from dictionary.database import get_db
from dictionary.models import Description, Word, WordDescription
from dictionary.schemas import (
    AllDescriptions,
    DescriptionModel,
    DescriptionReturn,
    DescriptionUpdate,
    WordDescriptionsModel,
)
from dictionary.utils import integrity_error_handler

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/descriptions", tags=["descriptions"])


db_dependency = Annotated[Session, Depends(get_db)]


@router.get(
    "/all",
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
    "/single/{desc_id}",
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


@router.post("/add/{word_id}", response_model=WordDescriptionsModel, status_code=201)
async def add_a_new_description(
    db: db_dependency, word_id: int, new_desc: DescriptionModel
):
    word = db.query(Word).filter_by(id=word_id).first()
    if not word:
        raise HTTPException(404, "Word not found.")

    try:
        description = Description(**new_desc.model_dump())
        db.add(description)
        db.commit()

        association_table = WordDescription(
            word_id=word_id, description_id=description.id
        )
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

    logger.debug("Description with id: %s was successfully created." % (description.id))

    return {"word": {"word": word.word, "id": word.id}, "description": desc}


@router.post(
    "/assign/{word_id}/{desc_id}",
    response_model=WordDescriptionsModel,
    status_code=201,
    description="Assign an existing description to the existing word.",
)
async def assign_description_to_a_word(db: db_dependency, word_id: int, desc_id: int):
    word = db.query(Word).filter_by(id=word_id).first()
    if not word:
        raise HTTPException(404, f"Word with the ID of {word_id} was not found.")

    description = db.query(Description).filter_by(id=desc_id).first()
    if not description:
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

    logger.debug(
        "Description with id: %s was successfully assigned to a word (id: %s)."
        % (description.id, word.id)
    )

    return {"word": {"word": word.word, "id": word.id}, "description": desc}


@router.patch(
    "/update/{desc_id}",
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


@router.delete("/delete/{desc_id}", status_code=204)
async def delete_a_description(db: db_dependency, desc_id: int):
    description = db.query(Description).filter_by(id=desc_id).first()
    if not description:
        raise HTTPException(404, f"Description with the ID: {desc_id} was not found.")

    db.delete(description)
    db.commit()

    logger.debug("Description with id: %s was successfully deleted." % (description.id))

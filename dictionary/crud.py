from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .database import get_db
from .models import Description, Word
from .schemas import (
    AllWords,
    DescriptionModel,
    DescriptionReturn,
    WordDescriptions,
    WordModel,
    WordReturn,
)

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
    db: db_dependency, id: int | None = None, search: str | None = None
):
    if not id and not search:
        raise HTTPException(400, "Either 'id' or 'search' parameter must be given.")

    if id:
        word = db.query(Word).filter_by(id=id).first()
        if not word:
            raise HTTPException(404, f"No word with ID of {id} stored in the database.")

        descriptions = db.query(Description).filter_by(word_id=word.id).all()
        if not descriptions:
            raise HTTPException(404, "No descriptions stored in the database.")

        translation_list = [desc.in_polish for desc in descriptions]

        return {"word": word.word, "translation": translation_list}

    words = db.query(Word).filter(Word.word.icontains(search)).all()
    if not words:
        raise HTTPException(404, f"No word '{search}' stored in the database.")

    results = []
    for record in words:
        descriptions = db.query(Description).filter_by(word_id=record.id).all()
        translation_list = (
            [desc.in_polish for desc in descriptions] if descriptions else []
        )
        results.append(
            {
                "word": {"word": record.word, "id": record.id},
                "translation": translation_list,
            }
        )

    return results


@router.get(
    "/word/{id}",
    response_model=WordDescriptions,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
    status_code=200,
    description="Get full information about the word by its ID.",
)
async def get_single_word(db: db_dependency, id: int):
    word = db.query(Word).filter_by(id=id).first()

    if not word:
        raise HTTPException(404, f"No word with ID of {id} stored in the database.")

    desc = db.query(Description).filter_by(word_id=id).all()

    return {"word": word, "description": desc}


@router.get(
    "/description/{id}",
    response_model=DescriptionReturn,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
    status_code=200,
)
async def get_single_description(db: db_dependency, id: int):
    desc = db.query(Description).filter_by(id=id).first()

    if not desc:
        raise HTTPException(404, "No desctiption stored in the database.")

    return desc


@router.post("/new_word", response_model=WordReturn, status_code=201)
async def add_a_new_word(db: db_dependency, new_word: WordModel):
    model = new_word.model_dump()
    word = Word(**model)

    db.add(word)
    db.commit()

    return word


@router.post("/new_description/{id}", response_model=DescriptionReturn, status_code=201)
async def add_a_new_description(db: db_dependency, id: int, new_desc: DescriptionModel):
    word = db.query(Word).filter_by(id=id).first()
    if not word:
        raise HTTPException(404, "Word not found.")

    desc = Description(**new_desc.model_dump(), word_id=id)

    db.add(desc)
    db.commit()

    return desc

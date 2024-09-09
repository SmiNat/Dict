from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .database import get_db
from .models import Description, Word
from .schemas import (
    DescriptionModel,
    DescriptionReturn,
    DictWord,
    DictWordShort,
    WordModel,
    WordReturn,
)

router = APIRouter(prefix="/dict", tags=["dict"])


db_dependency = Annotated[Session, Depends(get_db)]


@router.get("/all", response_model=None, status_code=200)
async def get_all_words(db: db_dependency):
    query = db.query(Word)

    if not query:
        raise HTTPException(404, "No words stored in the database.")

    return {"number of words": query.count(), "words list": query.all()}


@router.get("/word/{id}", response_model=DictWord, status_code=200)
async def get_single_word(db: db_dependency, id: int):
    word = db.query(Word).filter_by(id=id).first()

    if not word:
        raise HTTPException(404, "No word stored in the database.")

    desc = db.query(Description).filter_by(word_id=id).all()

    return {"word": word, "description": desc}


@router.get("/word/short/{id}", response_model=DictWordShort, status_code=200)
async def get_single_word_translations(db: db_dependency, id: int):
    word = db.query(Word).filter_by(id=id).first()

    if not word:
        raise HTTPException(404, "No word stored in the database.")

    descriptions = db.query(Description).filter_by(word_id=id).all()
    if not descriptions:
        raise HTTPException(404, "No descriptions stored in the database.")

    in_polish_list = [desc.in_polish for desc in descriptions]

    return {"word": word.word, "description": in_polish_list}


@router.get("/search", response_model=None, status_code=200)
async def get_search_word_translation(db: db_dependency, word: str):
    words = db.query(Word).filter(Word.word.icontains(word)).all()

    if not words:
        raise HTTPException(404, "No word stored in the database.")

    print("✅✅✅", word)

    desc_list = []
    for word in words:
        descriptions = db.query(Description).filter_by(word_id=word.id).all()
        in_polish_list = [desc.in_polish for desc in descriptions]
        desc_list.append(
            {"word": {"word": word.word, "id": word.id}, "description": in_polish_list}
        )

    return desc_list


@router.get("/description/{id}", response_model=DescriptionReturn, status_code=200)
async def get_single_description(db: db_dependency, id: int):
    desc = db.query(Description).filter_by(id=id).first()

    if not desc:
        raise HTTPException(404, "No desctiption stored in the database.")

    return desc


@router.post("/new_word", response_model=WordReturn, status_code=201)
async def add_new_word(db: db_dependency, new_word: WordModel):
    model = new_word.model_dump()
    word = Word(**model)

    db.add(word)
    db.commit()

    return word


@router.post("/new_description/{id}", response_model=DescriptionReturn, status_code=201)
async def add_new_description(db: db_dependency, id: int, new_desc: DescriptionModel):
    word = db.query(Word).filter_by(id=id).first()
    if not word:
        raise HTTPException(404, "Word not found.")

    desc = Description(**new_desc.model_dump(), word_id=id)

    db.add(desc)
    db.commit()

    return desc

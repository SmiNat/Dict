from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .database import get_db
from .models import Word
from .schemas import WordModel, WordReturn

router = APIRouter(prefix="/dict", tags=["dict"])


db_dependency = Annotated[Session, Depends(get_db)]


@router.get("/all", response_model=None, status_code=200)
async def get_all_words(db: db_dependency):
    query = db.query(Word)

    if not query:
        raise HTTPException(404, "No words stored in the database.")

    return {"number of words": query.count(), "words list": query.all()}


@router.post("/new_word", response_model=WordReturn, status_code=201)
async def add_new_word(db: db_dependency, new_word: WordModel):
    # word = Word(**new_word.model_dump())
    model = new_word.model_dump()
    word = Word(**model)

    db.add(word)
    db.commit()

    return word

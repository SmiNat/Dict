import logging
import random
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from dictionary.database import get_db
from dictionary.enums import MasterLevel
from dictionary.models import Word

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/shuffle", tags=["shuffle"])


db_dependency = Annotated[Session, Depends(get_db)]


class Shuffle:
    default_levels = {
        MasterLevel.NEW: 1.0,
        MasterLevel.MEDIUM: 0.8,
        MasterLevel.HARD: 1.5,
        MasterLevel.PERFECT: 0.3,
    }

    @classmethod
    def update_level(cls, level: MasterLevel, value: float):
        if value < 0 or value > 5:
            raise ValueError("The acceptable value range is from 0 to 5.0.")
        if level not in MasterLevel.list_of_values():
            raise TypeError(
                "Invalid level name. Acceptable levels: %s."
                % MasterLevel.list_of_values()
            )
        cls.default_levels[level] = value

    @classmethod
    def fetch_word(cls, db: Session):
        words = db.query(Word).with_entities(Word.word, Word.master_level).all()
        if not words:
            raise ValueError("No words found in the database.")

        word_with_weight_list = []
        for word in words:
            word_with_weight_list.append(
                (word[0], cls.default_levels.get(word[1], 1.0))
            )

        words_list, weights = zip(*word_with_weight_list)

        selected_word = random.choices(words_list, weights=weights, k=1)[0]

        return selected_word


@router.get("/lvl_weight/all")
async def get_level_weights():
    print("✅✅", Shuffle.default_levels)
    return Shuffle.default_levels


@router.post("/lvl_weight/update")
async def update_level_weight(
    level: MasterLevel, value: float = Query(default=1.0, ge=0, le=5)
):
    Shuffle.update_level(level, value)


@router.get("/all")
async def get_all(db: db_dependency):
    word = Shuffle.fetch_word(db)
    return {"word": word}

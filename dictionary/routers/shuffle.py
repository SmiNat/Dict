import logging
import random
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from dictionary.database import get_db
from dictionary.enums import MasterLevel
from dictionary.models import LevelWeight, Word
from dictionary.schemas import LevelReturn

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
    def populate_database(cls, db: Session):
        levels = db.query(LevelWeight).all()
        if not levels:
            for key, value in cls.default_levels.items():
                lvl = LevelWeight(level=key, default_weight=value)
                db.add(lvl)
                db.commit()
            levels = db.query(LevelWeight).all()
        return levels

    @classmethod
    def update_level(cls, db: Session, level: MasterLevel, value: float):
        if value < 0 or value > 5:
            raise ValueError("The acceptable value range is from 0 to 5.0.")
        if level not in MasterLevel.list_of_values():
            raise TypeError(
                "Invalid level name. Acceptable levels: %s."
                % MasterLevel.list_of_values()
            )

        db_level = db.query(LevelWeight).filter_by(level=level).first()
        if not db_level:
            raise ImportError("No level '%s' found in the database." % level)

        db_level.new_weight = value
        db.commit()
        db.refresh(db_level)

        logger.debug("Level '%s' weight updated to '%s'." % (level, value))

    @classmethod
    def fetch_word(cls, db: Session):
        cls.populate_database(db)

        words = db.query(Word).with_entities(Word.word, Word.master_level).all()
        if not words:
            raise ValueError("No words found in the database.")

        levels = (
            db.query(LevelWeight)
            .with_entities(
                LevelWeight.level, LevelWeight.default_weight, LevelWeight.new_weight
            )
            .all()
        )
        if not levels:
            raise ImportError("No word levels specified in the database.")
        level_weights = {}
        for level in levels:
            level_weights[level[0]] = {"default": level[1], "new": level[2]}

        logger.debug("Level weights: %s." % level_weights)

        word_with_weight_list = []
        for word in words:
            weights = db.query(LevelWeight).filter_by(level=word[1]).first()
            word_with_weight_list.append(
                # (word[0], cls.default_levels.get(word[1], 1.0))
                (
                    word[0],
                    weights.default_weight
                    if not weights.new_weight
                    else weights.new_weight,
                )
            )

        logging.debug("List of words with weights: %s." % word_with_weight_list)

        words_list, weights = zip(*word_with_weight_list)

        selected_word = random.choices(words_list, weights=weights, k=1)[0]

        return selected_word


@router.get("/all_levels", response_model=LevelReturn)
async def get_all_levels(db: db_dependency):
    levels = Shuffle.populate_database(db)
    return {"levels": levels}


@router.get("/levels/default")
async def get_default_level_weights():
    print("✅✅", Shuffle.default_levels)
    return Shuffle.default_levels


@router.get("/levels/current")
async def get_current_level_weights():
    # print("✅✅", Shuffle.default_levels)
    # return Shuffle.default_levels
    pass


@router.post("/lvl_weight/update")
async def update_level_weight(
    db: db_dependency, level: MasterLevel, value: float = Query(default=1.0, ge=0, le=5)
):
    Shuffle.update_level(db, level, value)


@router.get("/random")
async def get_random_word(db: db_dependency):
    word = Shuffle.fetch_word(db)
    return {"word": word}

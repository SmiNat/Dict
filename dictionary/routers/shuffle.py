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
    recent_words = []

    @classmethod
    def database_levels(cls, db: Session):
        levels = db.query(LevelWeight).all()
        if not levels:
            for level in MasterLevel:
                lvl = LevelWeight(level=level.value, default_weight=level.weight)
                db.add(lvl)
                db.commit()
            levels = db.query(LevelWeight).all()
        return levels

    @classmethod
    def update_recent_words(cls, word: str):
        word_list = cls.recent_words[:3]
        if word in word_list:
            raise ValueError("The word/sentence '%s' is already on the list." % word)
        word_list.insert(0, word)
        cls.recent_words = word_list[:3]

    @classmethod
    def update_level(cls, db: Session, level: MasterLevel, value: float):
        if value < 0 or value > 5:
            raise ValueError("The acceptable value range is from 0 to 5.0.")
        if level not in MasterLevel.list_of_values():
            raise TypeError(
                "Invalid level name. Acceptable levels: %s."
                % MasterLevel.list_of_values()
            )

        cls.database_levels(db)  # to make sure that db is populated with default levels

        db_level = db.query(LevelWeight).filter_by(level=level).first()
        if not db_level:
            raise ImportError("No level '%s' found in the database." % level)

        db_level.new_weight = value
        db.commit()
        db.refresh(db_level)

        logger.debug("Level '%s' weight updated to '%s'." % (level, value))

    @classmethod
    def fetch_word(cls, db: Session):
        # Extracting all words and levels from db
        words = db.query(Word).with_entities(Word.word, Word.master_level).all()
        if not words:
            raise ValueError("No words found in the database.")

        levels = cls.database_levels(db)
        if not levels:
            raise ImportError("No levels specified in the database.")

        # Mapping the levels with weights
        level_weights = {
            level.level: {"default": level.default_weight, "new": level.new_weight}
            for level in levels
        }
        logger.debug("Level weights: %s." % level_weights)

        # Creating a list of tuples with two values (word itself, level weight)
        word_with_weight_list = [
            (
                word[0],  # The word itself
                level_weights[word[1]]["new"]  # Use new_weight if set (not None)
                if level_weights[word[1]]["new"] is not None
                else level_weights[word[1]]["default"],  # Fall back to default_weight
            )
            for word in words
        ]
        logger.debug("List of words with weights: %s." % word_with_weight_list)

        # Unpacking the words and their corresponding weights into separate lists
        words_list, weights = zip(*word_with_weight_list)

        # Looping over the random words to add a new word to the recent_words list
        # Goal: if the database has more than 3 records, last 3 random words should be unique
        logger.debug("recent_words list at the beginning: %s" % cls.recent_words)
        if len(words) > 3:
            new_word = False
            while not new_word:
                selected_word = random.choices(words_list, weights=weights, k=1)[0]
                logger.debug("Random word: %s." % selected_word)
                try:
                    cls.update_recent_words(selected_word)
                    new_word = True
                except ValueError:
                    continue
        else:
            selected_word = random.choices(words_list, weights=weights, k=1)[0]
            cls.recent_words.insert(0, selected_word)
            cls.recent_words = cls.recent_words[:3]
        logger.debug("recent_words list at the end: %s" % cls.recent_words)

        return selected_word


@router.get("/all_levels", response_model=LevelReturn)
async def get_all_levels(db: db_dependency):
    levels = Shuffle.database_levels(db)
    return {"levels": levels}


@router.post("/lvl_weight/update")
async def update_level_weight(
    db: db_dependency, level: MasterLevel, value: float = Query(default=1.0, ge=0, le=5)
):
    Shuffle.update_level(db, level, value)


@router.get("/random")
async def get_random_word(db: db_dependency):
    word = Shuffle.fetch_word(db)
    return {"word": word}

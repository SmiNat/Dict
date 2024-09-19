import logging
import random
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from dictionary.database import get_db
from dictionary.enums import MasterLevel
from dictionary.exceptions import DatabaseError
from dictionary.models import Description, LevelWeight, Word
from dictionary.schemas import LevelReturn

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/shuffle", tags=["shuffle"])


db_dependency = Annotated[Session, Depends(get_db)]


class Shuffle:
    recent_words = []  # up to last 3 randomly selected words
    last_description = None

    @classmethod
    def database_levels(cls, db: Session):
        "Sets the default value of master levels."
        levels = db.query(LevelWeight).all()
        if not levels:
            for level in MasterLevel:
                lvl = LevelWeight(level=level.value, default_weight=level.weight)
                db.add(lvl)
                db.commit()
            levels = db.query(LevelWeight).all()
        return levels

    @classmethod
    def _update_recent_words(cls, word: str):
        "Updates recent_words class variable each time the fetch_word method is used."
        word_list = cls.recent_words[:3]
        if word in word_list:
            raise ValueError("The word/sentence '%s' is already on the list." % word)
        word_list.insert(0, word)
        cls.recent_words = word_list[:3]

    @classmethod
    def update_level(cls, db: Session, level: MasterLevel, value: float):
        """Sets a new value or updates the value of the master level weight.
        Default value is still preserved."""
        if value < 0 or value > 5:
            raise ValueError("The acceptable value range is from 0 to 5.0.")
        if level not in MasterLevel.list_of_values():
            raise DatabaseError(
                "Invalid level name. Acceptable levels: %s."
                % MasterLevel.list_of_values(),
                status_code=400,
            )

        cls.database_levels(db)  # to make sure that db is populated with default levels

        db_level = db.query(LevelWeight).filter_by(level=level).first()
        if not db_level:
            raise DatabaseError(
                "No '%s' level found in the database." % level.value, status_code=404
            )

        db_level.new_weight = value
        db.commit()
        db.refresh(db_level)

        logger.debug("Level '%s' weight updated to '%s'." % (level, value))

    @classmethod
    def fetch_word(cls, db: Session):
        """Extract random word/sentence from the database.
        The probability of extracting a word/sentence depends on the weight of
        the master level value.
        Returns description ID and description in Polish as a tuple."""
        # Extracting all words and levels from db
        words = (
            db.query(Word).with_entities(Word.id, Word.word, Word.master_level).all()
        )
        if not words:
            raise DatabaseError("No words found in the database.", status_code=404)

        levels = cls.database_levels(db)
        if not levels:
            raise DatabaseError("No levels specified in the database.", status_code=404)

        # Mapping the levels with weights
        level_weights = {
            level.level: {"default": level.default_weight, "new": level.new_weight}
            for level in levels
        }
        logger.debug("Level weights: %s." % level_weights)

        # Creating a list of tuples with two values (word itself, level weight)
        word_with_weight_list = [
            (
                (word.id, word.word),
                level_weights[word.master_level]["new"]  # Use new_weight if not None
                if level_weights[word.master_level]["new"] is not None
                else level_weights[word.master_level][
                    "default"
                ],  # Fall back to default_weight
            )
            for word in words
        ]
        logger.debug("List of words with weights: %s" % word_with_weight_list)

        # Unpacking the words and their corresponding weights into separate lists
        words_list, weights = zip(*word_with_weight_list)

        # Looping over the random words to add a new word to the recent_words list
        # Goal: if the database has more than 3 records, last 3 random words should be unique
        logger.debug("recent_words list at the beginning: %s" % cls.recent_words)
        if len(words) > 3:
            new_word = False
            while not new_word:
                selected_word = random.choices(words_list, weights=weights, k=1)[0]
                logger.debug(
                    "Random word: %s (ID: %s)" % (selected_word[1], selected_word[0])
                )
                try:
                    cls._update_recent_words(selected_word[1])
                    new_word = True
                except ValueError:
                    continue
        else:
            selected_word = random.choices(words_list, weights=weights, k=1)[0]
            cls.recent_words.insert(0, selected_word[1])
            cls.recent_words = cls.recent_words[:3]
        logger.debug("recent_words list at the end: %s" % cls.recent_words)

        return selected_word

    @classmethod
    def fetch_description(cls, db: Session):
        """Extract random description from the database.
        Returns description ID and description in Polish as a tuple."""
        descriptions = (
            db.query(Description)
            .with_entities(Description.id, Description.in_polish)
            .all()
        )
        if not descriptions:
            raise DatabaseError(
                "No descriptions found in the database.", status_code=404
            )

        new = False
        while not new:
            logger.debug("Last decription: %s" % cls.last_description)
            selected_description = random.choice(descriptions)
            if selected_description[1] != cls.last_description:
                cls.last_description = selected_description[1]
                new = True
        logger.debug("New decription: %s" % cls.last_description)

        return selected_description


@router.get("/all_levels", response_model=LevelReturn)
async def get_all_levels(db: db_dependency):
    levels = Shuffle.database_levels(db)
    return {"levels": levels}


@router.post("/lvl_weight/update")
async def update_level_weight(
    db: db_dependency,
    level: MasterLevel,
    value: float = Query(default=1.0, ge=0.0, le=5.0),
):
    Shuffle.update_level(db, level, value)


@router.get("/random_word")
async def get_random_word(db: db_dependency):
    try:
        word = Shuffle.fetch_word(db)
        return {"word": word[1], "id": word[0]}
    except DatabaseError as exc_info:
        raise HTTPException(
            exc_info.status_code if exc_info.status_code else 404, str(exc_info)
        )


@router.get("/random_desc")
async def get_random_description(db: db_dependency):
    try:
        desc = Shuffle.fetch_description(db)
        return {"description": desc[1], "id": desc[0]}
    except DatabaseError as exc_info:
        raise HTTPException(
            exc_info.status_code if exc_info.status_code else 404, str(exc_info)
        )

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import relationship
from sqlalchemy.types import TypeDecorator

from dictionary.database import Base
from dictionary.enums import MasterLevel, WordTypes


# Creating database tables
class StrippedString(TypeDecorator):
    """For stripping trailing and leading whitespaces from string values
    before saving a record to the database."""

    impl = String

    cache_ok = True

    def process_bind_param(self, value, dialect):
        # In case of nullable string fields and passing None
        return value.strip() if value else value

    def copy(self, **kw):
        return StrippedString(self.impl.length)


class Word(Base):
    __tablename__ = "word"

    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    word = Column(StrippedString(150), unique=True, nullable=False)
    master_level = Column(Enum(MasterLevel), default=MasterLevel.NEW)
    notes = Column(StrippedString(250))
    created = Column(DateTime, default=func.current_timestamp())
    updated = Column(
        DateTime, onupdate=func.current_timestamp(), default=func.current_timestamp()
    )

    # Relationship with WordDescription association table
    descriptions = relationship(
        "Description", secondary="word_description", back_populates="words"
    )


class Description(Base):
    __tablename__ = "description"

    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    type = Column(Enum(WordTypes))
    in_polish = Column(StrippedString(300), nullable=False, unique=True)
    in_english = Column(StrippedString(300))
    example = Column(StrippedString(300))
    created = Column(DateTime, default=func.current_timestamp())
    updated = Column(
        DateTime, onupdate=func.current_timestamp(), default=func.current_timestamp()
    )

    # Relationship with WordDescription association table
    words = relationship(
        "Word", secondary="word_description", back_populates="descriptions"
    )


class WordDescription(Base):
    __tablename__ = "word_description"

    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    word_id = Column(ForeignKey("word.id"), primary_key=True, nullable=False)
    description_id = Column(
        ForeignKey("description.id"), primary_key=True, nullable=False
    )
    created = Column(DateTime, default=func.current_timestamp())
    updated = Column(
        DateTime, onupdate=func.current_timestamp(), default=func.current_timestamp()
    )

    __table_args__ = (
        Index("idx_unique_word_description", word_id, description_id, unique=True),
    )


class LevelWeight(Base):
    __tablename__ = "level_weight"

    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    level = Column(Enum(MasterLevel), unique=True, nullable=False)
    default_weight = Column(Float, nullable=False)
    new_weight = Column(Float, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "default_weight >= 0 AND default_weight <= 5", name="check_default_weight"
        ),
        CheckConstraint("new_weight >= 0 AND new_weight <= 5", name="check_new_weight"),
    )

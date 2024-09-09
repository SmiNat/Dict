from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.types import TypeDecorator

from .database import Base
from .enums import MasterLevel, WordTypes


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
    __tablename__ = "words"

    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    word = Column(StrippedString(150), unique=True, nullable=False)
    master_level = Column(Enum(MasterLevel), default=MasterLevel.NEW)
    notes = Column(StrippedString(250))
    created = Column(DateTime, default=func.current_timestamp())
    updated = Column(DateTime, onupdate=func.current_timestamp())


class Description(Base):
    __tablename__ = "descriptions"

    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    type = Column(Enum(WordTypes))
    word_id = Column(ForeignKey("words.id"), primary_key=True)
    in_polish = Column(String(300), nullable=False)
    in_english = Column(String(300))
    example = Column(String(300))

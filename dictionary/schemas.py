import datetime

from pydantic import BaseModel, Field

from .enums import MasterLevel, WordTypes


class DescriptionModel(BaseModel):
    "Model for adding and updating descriptions."

    type: WordTypes | None = Field(default=None, examples=[None])
    in_polish: str
    in_english: str | None = Field(default=None, examples=[None])
    example: str | None = Field(default=None, examples=[None])

    class Config:
        use_enum_values = True
        from_attributes = True


class DescriptionWithId(DescriptionModel):
    "Model for returning descriptions with its ID."

    id: int


class DescriptionReturn(DescriptionWithId):
    "Model for returning descriptions with its ID and the ID of the word."

    word_id: int


class WordModel(BaseModel):
    "Model for adding and updating words/sentences."

    word: str
    master_level: MasterLevel = MasterLevel.NEW
    notes: str | None = Field(default=None, examples=[None])

    class Config:
        use_enum_values = True
        from_attributes = True


class WordReturn(WordModel):
    "Model for returning words with its ID and timestamps."

    id: int
    created: datetime.datetime
    updated: datetime.datetime

    class Config:
        from_attributes = True


class AllWords(BaseModel):
    "Model for returning all words stored in the database."

    number_of_words: int
    words: list[WordReturn]

    class Config:
        from_attributes = True


class WordDescriptions(BaseModel):
    "Model for returning word with its full descriptions."

    word: WordReturn
    description: list[DescriptionWithId]


class WordTranslations(BaseModel):
    "Model for returning word with its polish translation."

    word: str
    translation: list

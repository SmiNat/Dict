from pydantic import BaseModel, Field

from .enums import MasterLevel, WordTypes


class DescriptionModel(BaseModel):
    "Model for adding description to the database."

    type: WordTypes | None = Field(default=None, examples=[None])
    in_polish: str
    in_english: str | None = Field(default=None, examples=[None])
    example: str | None = Field(default=None, examples=[None])

    class Config:
        use_enum_values = True
        from_attributes = True


class DescriptionReturn(DescriptionModel):
    "Model for returning description with its ID."

    id: int
    # created: datetime.datetime
    # updated: datetime.datetime

    class Config:
        from_attributes = True


class DescriptionUpdate(DescriptionModel):
    "Model for updating description in the database."

    in_polish: str | None = Field(default=None, examples=[None])


class AllDescriptions(BaseModel):
    "Model for returning all descriptions stored in the database."

    number_of_descriptions: int
    descriptions: list[DescriptionReturn]

    class Config:
        from_attributes = True


class WordModel(BaseModel):
    "Model for adding word/sentence to the database."

    word: str
    master_level: MasterLevel = MasterLevel.NEW
    notes: str | None = Field(default=None, examples=[None])

    class Config:
        use_enum_values = True
        from_attributes = True


class WordReturn(WordModel):
    "Model for returning word with its ID and timestamps."

    id: int
    # created: datetime.datetime
    # updated: datetime.datetime


class WordUpdate(WordModel):
    "Model for updating word/sentence in the database."

    word: str | None = Field(default=None, examples=[None])
    master_level: MasterLevel | None = Field(default=None, examples=[None])


class AllWords(BaseModel):
    "Model for returning all words stored in the database."

    number_of_words: int
    words: list[WordReturn]

    class Config:
        from_attributes = True


class WordDescriptionsModel(BaseModel):
    "Model for returning word with its full descriptions."

    word: WordReturn
    description: list[DescriptionReturn]

    class Config:
        from_attributes = True

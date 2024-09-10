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


class DescriptionReturn(DescriptionModel):
    "Model for returning descriptions with its ID."

    id: int
    # created: datetime.datetime
    # updated: datetime.datetime

    class Config:
        from_attributes = True


class AllDescriptions(BaseModel):
    "Model for returning all descriptions stored in the database."

    number_of_descriptions: int
    descriptions: list[DescriptionReturn]

    class Config:
        from_attributes = True


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
    # created: datetime.datetime
    # updated: datetime.datetime


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

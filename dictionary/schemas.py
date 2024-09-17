from pydantic import BaseModel, ConfigDict, Field

from dictionary.enums import MasterLevel, WordTypes


class DescriptionModel(BaseModel):
    "Model for adding description to the database."

    type: WordTypes | None = Field(default=None, examples=[None])
    in_polish: str
    in_english: str | None = Field(default=None, examples=[None])
    example: str | None = Field(default=None, examples=[None])

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class DescriptionReturn(DescriptionModel):
    "Model for returning description with its ID."

    id: int
    # created: datetime.datetime
    # updated: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class DescriptionUpdate(DescriptionModel):
    "Model for updating description in the database."

    in_polish: str | None = Field(default=None, examples=[None])


class AllDescriptions(BaseModel):
    "Model for returning all descriptions stored in the database."

    number_of_descriptions: int
    descriptions: list[DescriptionReturn]

    model_config = ConfigDict(from_attributes=True)


class WordModel(BaseModel):
    "Model for adding word/sentence to the database."

    word: str
    master_level: MasterLevel = MasterLevel.NEW
    notes: str | None = Field(default=None, examples=[None])

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


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

    model_config = ConfigDict(from_attributes=True)


class WordDescriptionsModel(BaseModel):
    "Model for returning word with its full descriptions."

    word: WordReturn
    description: list[DescriptionReturn]

    model_config = ConfigDict(from_attributes=True)


class LevelWeightModel(BaseModel):
    "Model for returning levels with its weights."

    level: MasterLevel | None = Field(default=None, examples=[None])
    default_weight: float | int
    new_weight: float | int | None = None

    model_config = ConfigDict(from_attributes=True)


class LevelReturn(BaseModel):
    "Model for returning all levels stored in the database."

    levels: list[LevelWeightModel]

    model_config = ConfigDict(from_attributes=True)

import datetime

from pydantic import BaseModel, Field

from .enums import MasterLevel, WordTypes


class DescriptionModel(BaseModel):
    type: WordTypes | None = Field(default=None, examples=[None])
    in_polish: str
    in_english: str | None = Field(default=None, examples=[None])
    example: str | None = Field(default=None, examples=[None])

    class Config:
        use_enum_values = True
        from_attributes = True
        orm_mode = True


class DescriptionWithId(DescriptionModel):
    id: int

    class Config:
        use_enum_values = True


class DescriptionReturn(DescriptionWithId):
    word_id: int

    class Config:
        use_enum_values = True


class WordModel(BaseModel):
    word: str
    master_level: MasterLevel = MasterLevel.NEW
    notes: str | None = Field(default=None, examples=[None])

    class Config:
        use_enum_values = True
        from_attributes = True
        orm_mode = True


class WordReturn(WordModel):
    id: int
    created: datetime.datetime
    updated: datetime.datetime

    class Config:
        use_enum_values = True
        from_attributes = True
        orm_mode = True


class DictWord(BaseModel):
    word: WordReturn
    description: list[DescriptionWithId]


class DictWordShort(BaseModel):
    word: str
    description: list

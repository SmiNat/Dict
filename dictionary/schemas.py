import datetime

from pydantic import BaseModel, Field

from .enums import MasterLevel, WordTypes


class DescriptionModel(BaseModel):
    type: WordTypes | None = None
    in_polish: str
    in_english: str | None = None
    example: str | None = None

    class Config:
        use_enum_values = True
        from_attributes = True
        orm_mode = True


class DescriptionReturn(DescriptionModel):
    id: int
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
    description: list[DescriptionModel] = []
    created: datetime.datetime
    updated: datetime.datetime

    class Config:
        use_enum_values = True
        from_attributes = True
        orm_mode = True

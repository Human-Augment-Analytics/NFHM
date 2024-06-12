from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Specimen(BaseModel):
    key: str
    collectiondate: int
    highertaxon: str
    commonname: str
    scientificname: str
    recordedby: str | None = None
    location: list
    kingdom: str | None = None
    phylum: str | None = None
    class_: str = Field(default=None, alias='class')
    order: str | None = None
    family: str | None = None
    catalognumber: str
    earliest_epoch_or_lowest_series: str | None = None
    earliest_age_or_lowest_stage: str | None = None
    raw: Any
    access_rights: str | None = None
    media: Any
    model_config = ConfigDict(populate_by_name=True)

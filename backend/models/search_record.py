from datetime import date
from typing import Optional
from uuid import UUID

from geoalchemy2 import Geography
from geoalchemy2.shape import to_shape
from pydantic import computed_field
from pgvector.sqlalchemy import Vector
from sqlmodel import Field, SQLModel
from sqlalchemy import Column

class SearchRecord(SQLModel, table=True):
    __tablename__ = "search_records"
    __table_args__ = {"extend_existing": True}
    model_config = {
        "arbitrary_types_allowed": True
    }


    id: int = Field(default=None, primary_key=True)
    specimen_uuid: Optional[UUID] = Field(default=None, index=True)
    media_uuid: Optional[UUID] = Field(default=None, index=True)
    collection_date: Optional[date] = Field(default=None, index=True)
    higher_taxon: Optional[str] = Field(default=None, max_length=512)
    common_name: Optional[str] = Field(default=None, max_length=512, index=True)
    scientific_name: Optional[str] = Field(default=None, max_length=512, index=True)
    recorded_by: Optional[str] = Field(default=None, max_length=256)
    location: Optional[Geography] = Field(
        sa_column=Column(Geography(geometry_type='POINT', srid=4326)),
        default=None
    )
    tax_kingdom: Optional[str] = Field(default=None, max_length=128)
    tax_phylum: Optional[str] = Field(default=None, max_length=128)
    tax_class: Optional[str] = Field(default=None, max_length=128)
    tax_order: Optional[str] = Field(default=None, max_length=128)
    tax_family: Optional[str] = Field(default=None, max_length=128)
    tax_genus: Optional[str] = Field(default=None, max_length=128)
    catalog_number: Optional[str] = Field(default=None, max_length=128)
    earliest_epoch_or_lowest_series: Optional[str] = Field(default=None, max_length=512)
    earliest_age_or_lowest_stage: Optional[str] = Field(default=None, max_length=512)
    external_media_uri: Optional[str] = Field(default=None, max_length=2083)
    embedding: Optional[list[float]] = Field(default=None, sa_column=Column(Vector(512)))


    @computed_field
    @property
    def to_lat_long(self) -> dict[str, float]:
        if self.location:
            point = to_shape(self.location)
            return {'latitude': point.y, 'longitude': point.x}
        return {}
from pydantic import BaseModel
from typing import Optional

class Record(BaseModel):
    """
    Model for search records, containing parsed and embedded data from iDigBio, GBIF, and other external data sources on the web.

    Attributes:
        id (int): The unique identifier for the record.
        name (str): The name associated with the record.
        email (str): The email associated with the record.
    """
    id: int
    name: str
    scientific_name: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float] 
    description: Optional[str]
    image_source_name: Optional[str]
    specimen_source_name: Optional[str]
    external_id: str
    media_url: Optional[str]

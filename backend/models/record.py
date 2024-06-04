from pydantic import BaseModel


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
    uuid: str
    media_url: str

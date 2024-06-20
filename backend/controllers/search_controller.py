import json
import os
from typing import Optional, List

from fastapi import APIRouter, File, Form, UploadFile, HTTPException

from ..models.record import Record

file_path = os.path.join(os.path.dirname(__file__), "record_sample.json")
with open(file_path) as file:
    sample_data = json.load(file)

router = APIRouter()


@router.post("/search")
async def search(search_param: Optional[str] = Form(None), image: Optional[UploadFile] = File(None)):
    # For demonstration purposes, we'll just return the search_param and filename

    if search_param is None and image is None:
        raise HTTPException(status_code=400, detail="At least one of search_param or image must be provided.")

    records: List[Record] = [
        Record(
            id=index + 1,
            name=item.get("name", ""),
            scientific_name=item.get("scientific_name", ""),
            latitude=item.get("latitude", 0.0),
            longitude=item.get("longitude", 0.0),
            description=item.get("description", ""),
            image_source_name=item.get("image_source_name", ""),
            specimen_source_name=item.get("specimen_source_name", ""),
            external_id=item.get("id"),
            media_url=item.get("media_url", None)
        )
        for index, item in enumerate(sample_data)
    ]
    return {
        "search_param": search_param,
        "filename": image and image.filename,
        "record_count": len(records),
        "records": records
    }

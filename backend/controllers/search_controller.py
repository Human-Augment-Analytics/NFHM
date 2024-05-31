from fastapi import APIRouter, File, Form, UploadFile
from pydantic import BaseModel
from typing import Optional
from models.record import Record

router = APIRouter()

@router.post("/search")
async def search(search_param: str = Form(...), image: UploadFile = File(...)):
    # For demonstration purposes, we'll just return the search_param and filename
    records = [
        Record(id=1,
               name="Specimen from the Natural History Museum of Los Angeles, Invertebrate Paleontology Department (LACMIP).",
               uuid='foo',
               media_url='http://digitalgallery.nhm.org:8085/invertpaleo_nhm/api/v1/asset/771612/preview'
               ),
        Record(id=2,
               name="Specimen from the Natural History Museum of Los Angeles, Invertebrate Paleontology Department (LACMIP).",
               uuid='foo-bar',
               media_url='http://digitalgallery.nhm.org:8085/invertpaleo_nhm/api/v1/asset/752617/preview'
               ),
        Record(id=3,
               name="Specimen from the Natural History Museum of Los Angeles, Invertebrate Paleontology Department (LACMIP).",
               uuid='foo-bar-baz',
               media_url='http://digitalgallery.nhm.org:8085/invertpaleo_nhm/api/v1/asset/771612/preview'
               ),
    ]
    return {
        "search_param": search_param,
        "filename": image.filename,
        "record_count": len(records),
        "records": records
    }

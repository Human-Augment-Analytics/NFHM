import logging
from typing import Optional, List, AsyncGenerator
from fastapi import APIRouter, File, Form, UploadFile, Depends, HTTPException, Request, Query
from sqlmodel import select
import torch
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy import func, cast
from pgvector.sqlalchemy import Vector
from PIL import Image
import io
from datetime import date
from uuid import UUID
from pydantic import BaseModel, Field
from models.search_record import SearchRecord

logger = logging.getLogger(__name__)

router = APIRouter()

class RecordPayload(BaseModel):
    id: int
    scientific_name: Optional[str] = None
    common_name: Optional[str] = None
    name: str
    description: str
    image_source_name: str = ""
    specimen_source_name: str = ""
    external_id: Optional[UUID] = None
    media_url: str
    specimen_id: Optional[UUID] = None
    recorded_by: Optional[str] = None
    collection_date: Optional[date] = None
    source: str = "iDigBio"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    model: str
    pretrained: str
    embed_version: str

class SearchResponse(BaseModel):
    search_param: Optional[str] = None
    filename: Optional[str] = None
    record_count: int
    records: List[RecordPayload]
    embed_version: str

async def get_session(request: Request) -> AsyncGenerator[AsyncSession, None]:
    engine: AsyncEngine = request.app.state.db_engine
    async with AsyncSession(engine) as session:
        yield session

@router.post("/search", response_model=SearchResponse)
async def search(
    request: Request,
    search_param: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    limit: int = Query(30, ge=1, le=100),
    embed_version: str = Query("default", max_length=512),
    session: AsyncSession = Depends(get_session)
) -> SearchResponse:
    try:
        if search_param is None and image is None:
            raise HTTPException(status_code=400, detail="At least one of search_param or image must be provided.")

        search_vector = await process_input(request, search_param, image)

        query = select(SearchRecord).where(
            SearchRecord.embed_version == embed_version
        ).order_by(
            func.l2_distance(
                SearchRecord.embedding,
                cast(search_vector, Vector)
            )
        ).limit(limit)

        results = await session.execute(query)
        records = results.scalars().all()

        payload = [create_record_payload(record) for record in records if record.external_media_uri is not None]

        return SearchResponse(
            search_param=search_param,
            filename=image.filename if image else None,
            record_count=len(payload),
            records=payload,
            embed_version=embed_version
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during search: {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred during the search process.")

async def process_input(request: Request, search_param: Optional[str], image: Optional[UploadFile]) -> List[float]:
    try:
        app = request.app
        if image:
            contents = await image.read()
            img = Image.open(io.BytesIO(contents))
            img_preprocessed = app.state.preprocess(img).unsqueeze(0).to(app.state.device)
            with torch.no_grad(), torch.autocast(device_type='cuda', dtype=torch.float16):
                image_features = app.state.model.encode_image(img_preprocessed)
                return image_features.cpu().numpy()[0].tolist()
        else:
            with torch.no_grad(), torch.autocast(device_type='cuda', dtype=torch.float16):
                text = app.state.tokenizer([search_param]).to(app.state.device)
                text_features = app.state.model.encode_text(text)
                return text_features.cpu().numpy()[0].tolist()
    except Exception as e:
        logger.error(f"Error processing input: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred while processing the input.")

def create_record_payload(record: SearchRecord) -> RecordPayload:
    return RecordPayload(
        id=record.id,
        scientific_name=record.scientific_name,
        common_name=record.common_name,
        name=record.common_name or record.scientific_name or "",
        description=record.common_name or record.scientific_name or "",
        external_id=record.media_uuid,
        media_url=record.external_media_uri or "",
        specimen_id=record.specimen_uuid,
        recorded_by=record.recorded_by,
        collection_date=record.collection_date,
        model=record.model,
        pretrained=record.pretrained,
        embed_version=record.embed_version,
        **record.to_lat_long
    )
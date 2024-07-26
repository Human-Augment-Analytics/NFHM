from typing import Optional, List, Any
from fastapi import APIRouter, File, Form, UploadFile, Depends, HTTPException, Request
from sqlmodel import select
import torch
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import func, cast
from pgvector.sqlalchemy import Vector
from PIL import Image
import io
from models.search_record import SearchRecord


router = APIRouter()

DATABASE_URL = "postgresql+asyncpg://postgres:postgres@postgres/nfhm"
engine = create_async_engine(DATABASE_URL, echo=True)


async def get_session():
    async with AsyncSession(engine) as session:
        yield session


@router.post("/search")
async def search(
    request: Request,
    search_param: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    limit=30,
    session: AsyncSession = Depends(get_session)
):
    # For demonstration purposes, we'll just return the search_param and filename
    app = request.app
    if search_param is None and image is None:
        raise HTTPException(status_code=400, detail="At least one of search_param or image must be provided.")

    # Convert input to vector
    if image:
        # Process the image
        contents = await image.read()
        img = Image.open(io.BytesIO(contents))
        img_preprocessed = app.preprocess(img).unsqueeze(0).to(app.device)
        with torch.no_grad(), torch.cuda.amp.autocast():
            image_features = app.model.encode_image(img_preprocessed)
            search_vector = image_features.cpu().numpy()[0].tolist()
    else:
        # Process the text
        with torch.no_grad(), torch.cuda.amp.autocast():
            text = app.tokenizer([search_param]).to(app.device)
            text_features = app.model.encode_text(text)
            search_vector = text_features.cpu().numpy()[0].tolist()

    # Construct the query using SQLModel
    # query = select(SearchRecord).order_by(
    #     cosine_distance(SearchRecord.embedding, search_vector)
    # ).limit(limit)
    # query = select(SearchRecord).order_by(
    #     func.l2_distance(SearchRecord.embedding, search_vector)
    # ).limit(limit)

    query = select(SearchRecord).order_by(
        func.l2_distance(
            SearchRecord.embedding,
            cast(search_vector, Vector)
        )
    ).limit(limit)

    # Execute the query
    results = await session.exec(query)
    records = results.all()

    payload: List[Any] = [
        {
            "id": record.id,
            "scientific_name": record.scientific_name,
            "common_name": record.common_name,
            "name": record.common_name,
            # "similarity": 1 - cosine_distance(record.embedding, search_vector)
            "description": record.common_name,
            "image_source_name": "",
            "specimen_source_name": "",
            "external_id": record.media_uuid,
            "media_url": record.external_media_uri,
            "specimen_id": record.specimen_uuid,
            "recorded_by": record.recorded_by,
            "collection_date": record.collection_date,
            # TODO make this a field within the data
            "source": "iDigBio",
            **record.to_lat_long
        }
        for record in records
    ]

    return {
        "search_param": search_param,
        "filename": image and image.filename,
        "record_count": len(payload),
        "records": payload
    }

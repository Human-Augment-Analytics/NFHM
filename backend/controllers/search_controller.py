import json
import os
from typing import Optional, List, Any
from fastapi import APIRouter, File, Form, UploadFile, Depends, HTTPException
from sqlmodel import Field, SQLModel, Session, select
import torch
import open_clip
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import func, cast, ARRAY, Float
from pgvector.sqlalchemy import Vector
from PIL import Image
import io
from ..models.search_record import SearchRecord


from models.record import Record

# # file_path = os.path.join(os.path.dirname(__file__), "record_sample.json")
# # with open(file_path) as file:
# #     sample_data = json.load(file)

router = APIRouter()

DATABASE_URL = "postgresql+asyncpg://postgres:postgres@postgres/nfhm"
engine = create_async_engine(DATABASE_URL, echo=True)

async def get_session():
    async with AsyncSession(engine) as session:
        yield session

# device = "cuda" if torch.cuda.is_available() else "cpu"
if torch.backends.mps.is_available():
    device = torch.device("mps:0")
    print("Using MPS")
else:
    device = torch.device("cpu")
model, _, preprocess = open_clip.create_model_and_transforms('ViT-B-32', pretrained='laion2b_s34b_b79k', device=device)
model = model.to(device)
tokenizer = open_clip.get_tokenizer('ViT-B-32')


@router.post("/search")
async def search(
    search_param: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    limit=30,
    session: AsyncSession = Depends(get_session)):
    # For demonstration purposes, we'll just return the search_param and filename

    if search_param is None and image is None:
        raise HTTPException(status_code=400, detail="At least one of search_param or image must be provided.")

    # Convert input to vector
    if image:
        # Process the image
        contents = await image.read()
        img = Image.open(io.BytesIO(contents))
        img_preprocessed = preprocess(img).unsqueeze(0).to(device)
        with torch.no_grad(), torch.cuda.amp.autocast():
            image_features = model.encode_image(img_preprocessed)
            search_vector = image_features.cpu().numpy()[0].tolist()
    else:
        # Process the text
        with torch.no_grad(), torch.cuda.amp.autocast():
            text = tokenizer([search_param]).to(device)
            text_features = model.encode_text(text)
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
            "latitude": "",
            "longitude": "",
            "description": record.common_name,
            "image_source_name": "",
            "specimen_source_name": "",
            "external_id": record.media_uuid,
            "media_url": record.external_media_uri

        }
        for record in records
    ]

    return  {
        "search_param": search_param,
        "filename": image and image.filename,
        "record_count": len(payload),
        "records": payload
    }

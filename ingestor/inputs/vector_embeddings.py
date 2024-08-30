import traceback
import numpy as np
from numpy.typing import NDArray
import aiohttp
import asyncio
import json
import torch
import open_clip
from dateutil import parser as date_parser
from PIL import Image
from io import BytesIO
import logging
from typing import Any, List, Dict, Optional
from schema.processed_search_record import ProcessedSearchRecord

logger = logging.getLogger("vector_embedder")
logging.getLogger("PIL.TiffImagePlugin").setLevel(logging.INFO)
logging.getLogger("pymongo.command").setLevel(logging.INFO)
logging.getLogger("pymongo.serverSelection").setLevel(logging.INFO)

model = None
preprocess = None
tokenizer = None
device = (
    torch.device("mps:0") if torch.backends.mps.is_available() else torch.device("cpu")
)

logger.info(f"Using device: {device}")


async def load_model():
    global model, preprocess, tokenizer
    if model is None:
        model, _, preprocess = open_clip.create_model_and_transforms(
            "ViT-B-32", pretrained="laion2b_s34b_b79k", device=device
        )
        model.to(device)
        model.eval()
        tokenizer = open_clip.get_tokenizer("ViT-B-32")
        logger.info("Model loaded")
    else:
        logger.info("Model already loaded")


def input_data_mapper(
    media: Dict[str, Any], line: Dict[str, Any]
) -> ProcessedSearchRecord:
    record: ProcessedSearchRecord = {
        "specimen_uuid": line.get("uuid", ""),
        "scientific_name": line.get("data", {}).get("dwc:scientificName")
        or line.get("data", {}).get("dwc:genus"),
        "external_media_uri": media.get("data", {}).get("ac:accessURI")
        or media.get("indexTerms", {}).get("accessuri"),
        "media_uuid": media.get("uuid"),
        "catalog_number": line.get("data", {}).get("dwc:catalogNumber"),
        "recorded_by": line.get("data", {}).get("dwc:recordedBy"),
        "tax_kingdom": line.get("data", {}).get("dwc:kingdom"),
        "tax_phylum": line.get("data", {}).get("dwc:phylum"),
        "tax_class": line.get("data", {}).get("dwc:class"),
        "tax_order": line.get("data", {}).get("dwc:order"),
        "tax_family": line.get("data", {}).get("dwc:family"),
        "tax_genus": line.get("data", {}).get("dwc:genus"),
        "common_name": line.get("indexTerms", {}).get("commonname"),
        "higher_taxon": line.get("indexTerms", {}).get("highertaxon"),
        "earliest_epoch_or_lowest_series": line.get("indexTerms", {}).get(
            "earliestepochorlowestseries"
        )
        or line.get("data", {}).get("dwc:earliestEpochOrLowestSeries"),
        "earliest_age_or_lowest_stage": line.get("indexTerms", {}).get(
            "earliestageorloweststage"
        )
        or line.get("data", {}).get("dwc:dwc:earliestAgeOrLowestStage"),
        "collection_date": None,
        "location": None,
        "embedding": None,
        "tensor_embedding": None,
    }

    geopoint = line.get("indexTerms", {}).get("geopoint", {})
    if geopoint.get("lon") is not None and geopoint.get("lat") is not None:
        record["location"] = f"POINT({geopoint['lon']} {geopoint['lat']})"

    collection_date = line.get("indexTerms", {}).get("datecollected")
    if collection_date is not None:
        try:
            parsed_date = date_parser.parse(collection_date)
            record["collection_date"] = parsed_date.date()
        except ValueError:
            logger.warning(
                f"Invalid date format for collection_date: {collection_date}"
            )

    return record


async def extract_data(
    collection: Any, page_size: int, page_offset: int
) -> List[ProcessedSearchRecord]:
    projection = {
        "uuid": 1,
        "media.uuid": 1,
        "media.data": 1,
        "media.indexTerms": 1,
        "media.ac:accessURI": 1,
        "data.dwc:scientificName": 1,
        "data.dwc:genus": 1,
        "data.dwc:family": 1,
        "data.dwc:order": 1,
        "data.dwc:class": 1,
        "data.dwc:phylum": 1,
        "data.dwc:kingdom": 1,
        "data.dwc:catalogNumber": 1,
        "data.dwc:recordedBy": 1,
        "indexTerms.highertaxon": 1,
        "indexTerms.commonname": 1,
        "indexTerms.geopoint": 1,
        "indexTerms.earliestepochorlowestseries": 1,
        "indexTerms.earliestageorloweststage": 1,
        "indexTerms.datecollected": 1,
    }

    query = {}
    cursor = (
        collection.find(query, projection)
        .sort("_id", 1)
        .skip(page_offset * page_size)
        .limit(page_size)
    )

    documents = await cursor.to_list(length=page_size)
    return [
        input_data_mapper(media, document)
        for document in documents
        for media in document["media"]
    ]


async def download_image(
    session: aiohttp.ClientSession, image_location: str
) -> Optional[Image.Image]:
    try:
        async with session.get(image_location, allow_redirects=True) as response:
            if response.status < 400:
                content = await response.read()
                return Image.open(BytesIO(content))
            else:
                logger.error(
                    f"Failed to download image from {image_location}. Status code: {response.status}"
                )
                return None
    except Exception as e:
        logger.error(f"Error downloading image from {image_location}: {e}")
        return None


async def process_image(
    session: aiohttp.ClientSession, record: ProcessedSearchRecord
) -> ProcessedSearchRecord:
    image_location = record["external_media_uri"]
    if image_location:
        img = await download_image(session, image_location)
        if img is not None:
            image = preprocess(img).unsqueeze(0).to(device)
            with torch.no_grad():
                vector = model.encode_image(image)
            vector = vector.cpu()
            record["tensor_embedding"] = vector
        else:
            logger.error(f"No image downloaded for: {image_location}")
    else:
        logger.error("No external_media_uri provided in the record")

    return record


async def vector_embedder(
    args: str, opts: Dict[str, Any]
) -> List[ProcessedSearchRecord]:
    try:
        params = json.loads(args)
        collection = opts["mongo_collection"]
        queue = opts["queue"]
        page_size = params.get("page_size", 100)
        page_offset = params.get("page_offset", 0)

        await load_model()

        mongo_records = await extract_data(collection, page_size, page_offset)

        if len(mongo_records) >= page_size:
            next_job = {"page_size": page_size, "page_offset": page_offset + 1}
            logger.info(f"Enqueuing next job with offset {page_offset + 1}")
            await queue.enqueue("embedder", json.dumps(next_job))

        batch_size = 10
        results: List[ProcessedSearchRecord] = []

        async with aiohttp.ClientSession() as session:
            for i in range(0, len(mongo_records), batch_size):
                chunk = mongo_records[i : i + batch_size]
                tasks = [process_image(session, record) for record in chunk]
                processed_records = await asyncio.gather(*tasks)

                for record in processed_records:
                    if (
                        record["tensor_embedding"] is not None
                        and record["tensor_embedding"].numel() > 0
                    ):
                        row: torch.Tensor = torch.nn.functional.normalize(
                            record["tensor_embedding"]
                        )
                        numpy_row: NDArray[np.float32] = np.asarray(
                            row.detach().cpu(), dtype=np.float32
                        )
                        record["embedding"] = json.dumps(numpy_row.tolist()[0])
                        results.append(record)
                    else:
                        logger.error(
                            f"No vector for image: {record['external_media_uri']}"
                        )

        logger.info(f"Finished processing {len(results)} images")
        return results

    except Exception as e:
        logger.error(f"Encountered an error in vector_embedder: {e}")
        traceback.print_exc()
        return []

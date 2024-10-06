import traceback
import numpy as np
from numpy.typing import NDArray
from aiohttp import ClientSession, ClientTimeout
from aiohttp.client_exceptions import ServerDisconnectedError
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

DEFAULT_OPEN_CLIP_MODEL = "ViT-B-32"
DEFAULT_OPEN_CLIP_PRETRAIN_DATA = "laion2b_s34b_b79k"
DEFAULT_EMBED_VERSION = "default"

model = None
preprocess = None
tokenizer = None
device = (
    torch.device("mps:0" if torch.backends.mps.is_available() else "cuda" if torch.cuda.is_available() else "cpu")
)

logger.info(f"Using device: {device}")


async def load_model(model_name: str = DEFAULT_OPEN_CLIP_MODEL, pretrained: str = DEFAULT_OPEN_CLIP_PRETRAIN_DATA):
    global model, preprocess, tokenizer
    if model is None:
        model, _, preprocess = open_clip.create_model_and_transforms(
            model_name, pretrained=pretrained, device=device
        )
        model.to(device)
        model.eval()
        tokenizer = open_clip.get_tokenizer(model_name)
        logger.info(f"Model loaded: {model_name}, pretrained: {pretrained}")
    else:
        logger.info("Model already loaded")



def input_data_mapper(
    media: Dict[str, Any], line: Dict[str, Any], model_name: str, pretrained: str, embed_version: str = DEFAULT_EMBED_VERSION
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
        "model": model_name,
        "pretrained": pretrained,
        "embed_version": embed_version,
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
    collection: Any, page_size: int, page_offset: int, model_name: str, pretrained: str, embed_version: str
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
        input_data_mapper(media, document, model_name, pretrained, embed_version)
        for document in documents
        for media in document["media"]
    ]


async def download_image(
    session: aiohttp.ClientSession, image_location: str, timeout: int = 30
) -> Optional[Image.Image]:
    try:
        # Set a timeout for the request
        timeout_obj = ClientTimeout(total=timeout)
        
        async with session.get(image_location, allow_redirects=True, timeout=timeout_obj) as response:
            if response.status < 400:
                content = await response.read()
                try:
                    return Image.open(BytesIO(content))
                except IOError as io_err:
                    logger.error(f"Error opening image from {image_location}: {io_err}")
                    return None
            else:
                logger.error(
                    f"Failed to download image from {image_location}. Status code: {response.status}, "
                    f"Reason: {response.reason}, Headers: {response.headers}"
                )
                return None
    except asyncio.TimeoutError:
        logger.error(f"Timeout error downloading image from {image_location}")
        return None
    except aiohttp.ClientError as client_err:
        logger.error(
            f"Client error downloading image from {image_location}: {client_err}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error downloading image from {image_location}: {e}", exc_info=True)
        return None

async def download_with_exponential_backoff(
    session: ClientSession, 
    url: str, 
    max_retries: int = 5, 
    base_delay: float = 1.0, 
    max_delay: float = 60.0
) -> Optional[Image.Image]:
    for attempt in range(max_retries):
        try:
            return await download_image(session, url)
        except ServerDisconnectedError as e:
            if attempt == max_retries - 1:
                logger.error(f"Max retries reached for {url}: {e}")
                return None
            
            # Calculate delay with exponential backoff and jitter
            delay = min(base_delay * (2 ** attempt) + random.uniform(0, 1), max_delay)
            
            logger.warning(f"Server disconnected for {url}, retrying in {delay:.2f} seconds... (Attempt {attempt + 1}/{max_retries})")
            await asyncio.sleep(delay)
    
    logger.error(f"Failed to download image from {url} after {max_retries} attempts")
    return None


async def process_image(
    session: aiohttp.ClientSession, record: ProcessedSearchRecord
) -> ProcessedSearchRecord:
    image_location = record["external_media_uri"]
    if image_location:
        img = await download_with_exponential_backoff(session, image_location)
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
        cv_model =  params.get('model') or opts.get('model', DEFAULT_OPEN_CLIP_MODEL)
        pretrained = params.get('pretrained') or opts.get('pretrained', DEFAULT_OPEN_CLIP_PRETRAIN_DATA)
        embed_version = params.get('embed_version') or opts.get('embed_version', DEFAULT_EMBED_VERSION)

        await load_model(model_name=cv_model, pretrained=pretrained)

        mongo_records = await extract_data(collection, page_size, page_offset, cv_model, pretrained, embed_version)

        if len(mongo_records) >= page_size:
            next_job = {
                "page_size": page_size, 
                "page_offset": page_offset + 1,
                "model": cv_model,
                "pretrained": pretrained,
                "embed_version": embed_version
            }
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

import traceback
import math
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import aiohttp
import requests
from PIL import Image
from io import BytesIO
from logging import getLogger
from typing import Any
import asyncio
import json
import torch
import open_clip
from datetime import datetime
from bson.objectid import ObjectId

logger = getLogger('vector_embedder')

model = None
preprocess = None
tokenizer = None
device = None

if torch.backends.mps.is_available():
    device = torch.device("mps:0")
    logger.info("Using MPS")
else:
    device = torch.device("cpu")

async def load_model():
    """
    Loads the pre-trained model and tokenizer for vector embeddings.
    This is lazily evaluated once when the first call to vector_embedder is made.
    Loading the model is a slow operation that breaks ingestor.py when done at the top level upon import
    """
    global model, preprocess, tokenizer, device
    # if model is not None:
    model, _, preprocess = open_clip.create_model_and_transforms('ViT-B-32', pretrained='laion2b_s34b_b79k', device=device)
    model.to(device)
    model.eval()  # model in train mode by default, impacts some models with BatchNorm or stochastic depth active
    tokenizer = open_clip.get_tokenizer('ViT-B-32')
    logger.info("Model loaded")
    # else:
        # logger.info("Model loaded already")

def input_data_mapper(media: dict, line: dict) -> dict:
    tmp_d = {
        "specimen_uuid": line.get("uuid"),
        "scientific_name": line.get("data", {}).get("dwc:scientificName") or line.get("data", {}).get("dwc:genus"),
        "external_media_uri": media.get("data", {}).get("ac:accessURI") or media.get("indexTerms", {}).get("accessuri"),
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
        "earliest_epoch_or_lowest_series": line.get("indexTerms", {}).get("earliestepochorlowestseries") or line.get("data", {}).get("dwc:earliestEpochOrLowestSeries"),
        "earliest_age_or_lowest_stage": line.get("indexTerms", {}).get("earliestageorloweststage") or line.get("data", {}).get("dwc:dwc:earliestAgeOrLowestStage"),
        "collection_date": line.get("indexTerms", {}).get("datecollected")
    }

    if line.get("indexTerms", {}).get("geopoint", {}).get("lon") is not None:
        lat = str(line.get("indexTerms", {}).get("geopoint", {}).get("lat"))
        lon = str(line.get("indexTerms", {}).get("geopoint", {}).get("lon"))
        tmp_d["location"] = f"POINT({lon} {lat})"

    if tmp_d["collection_date"] is not None:
        tmp_d["collection_date"] = datetime.strptime('2012-01-12', '%Y-%m-%d');

    return tmp_d


async def extract_data(collection: Any, page_size: int, page_offset: int):
    projection = {
        "uuid": 1,
        "media.uuid": 1,
        "media.data": 1,
        "media.indexTerms": 1,
        "media.ac:accessURI": 1,
        "data.dwc:scientificName":  1,
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
        "indexTerms.datecollected": 1
    }



    query = {}
    # TODO: Turn the following comment into a command line example.
    # If you're trying to re-start a job that's already proceeded for some time, and want to avoid redundant work
    # You can uncomment the below line and replace the ObjectId with the last _id you processed, which can be found by looking 
    # at the speciemen_uuid of the last record in PG and then mapping that to what's in the mongo collection to get the Mongo document object id
    # query = {"_id": {"$gt": ObjectId("66882305ffdc56ce50b64652") }}
    # // For sake of efficency, make sure sort is on an indexed field, otherwise skip will become very slow
    cursor = collection.find(query, projection).sort({ "_id": 1 }).skip(page_offset * page_size).limit(page_size)
    new_lines = []
    for document in await cursor.to_list(length=page_size):
        for media in document['media']:
            data = input_data_mapper(media, document)
            new_lines.append(data)
    
    return new_lines

async def download_image_and_preprocess(entry: dict) -> torch.Tensor:
    """This method downloads an image asynchronously and outputs its vector in memory"""
    image_location = entry['external_media_uri']

    # import pprint
    # pprint.pp(entry)
    logger.info("Begin downloading image from {}".format(entry))

    async with aiohttp.ClientSession() as session:
        async with session.get(image_location, allow_redirects=True) as response:
            try: 
                if response.status < 400:
                    content = await response.read()
                    logger.debug(f"Downloaded image from {image_location}")
                    img = Image.open(BytesIO(content))
                    logger.debug(f"Opened image from {image_location}")
                    image = preprocess(img).unsqueeze(0).to(device)
                    logger.debug(f"Preprocessed image from {image_location}")
                    vector = model.encode_image(image)
                    vector = vector.cpu()
                    logger.debug(f"Encoded image from {image_location}")
                else:
                    logger.error(f"Failed to download image from {image_location}. Status code: {response.status}")
                    vector = None
            except Exception as e:
                logger.error(e)
                logger.error(f"Error downloading image from {image_location}")
                vector = None
            entry['tensor_embedding'] = vector
            return entry


async def vector_embedder(args: str, opts: dict) -> list[dict[Any, Any]]:
    try:
        params = json.loads(args)
        collection = opts['mongo_collection']
        queue = opts['queue']
        page_size = params.get('page_size', 100)
        page_offset = params.get('page_offset', 0)

        if model is None:
            await load_model()

        mongo_records = await extract_data(collection, page_size, page_offset)

        # Greater than or equal because we extract the nested media data from each record, so there's more possibly than page_size mongo_records
        if len(mongo_records) >= page_offset:
            next_job = { 'page_size': page_size, 'page_offset': page_offset + 1 }
            await queue.enqueue('embedder', json.dumps(next_job))

        batch_size=10
        num_chunks = math.ceil(len(mongo_records)/batch_size)

        results = []
        for chunk in np.array_split(mongo_records, num_chunks):
            # MULTITHREADED
            # with ThreadPoolExecutor(max_workers=3) as executor:
            #     loop = asyncio.get_running_loop()
            #     # Wrap download_image_and_preprocess with asyncio.run_coroutine_threadsafe
            #     tasks = [loop.run_in_executor(executor, lambda entry=entry: asyncio.run_coroutine_threadsafe(download_image_and_preprocess(entry), loop).result()) for entry in chunk]
            #     entries_with_embeddings = await asyncio.gather(*tasks)
            #     # downloaded_images = list(executor.map(download_image_and_preprocess, chunk))

            #     # downloaded_images = executor.map(download_image_and_preprocess, entry)
            #     for _i, record in enumerate(entries_with_embeddings):
            #         image = record['tensor_embedding']
            #         try:
            #             if image is not None and image.numel() > 0:
            #                 row = torch.nn.functional.normalize(image)
            #                 row = row.detach().numpy().tolist()[0]
            #                 vector = json.dumps(row)

            #                 record['embedding'] = vector
            #                 results.append(record)
            #             else:
            #                 logger.error("{}: No vector for image".format(record['media_location']))
            #         except Exception as e:
            #             logger.error(e)


            # SINGLE THREADED
            tasks = [download_image_and_preprocess(entry) for entry in chunk]

            entries_with_embeddings = await asyncio.gather(*tasks)
            # downloaded_images = list(executor.map(download_image_and_preprocess, chunk))

            # downloaded_images = executor.map(download_image_and_preprocess, entry)
            for _i, record in enumerate(entries_with_embeddings):
                image = record['tensor_embedding']
                try:
                    if image is not None and image.numel() > 0:
                        image = image.cpu()
                        row = torch.nn.functional.normalize(image)
                        row = row.detach().numpy().tolist()[0]
                        vector = json.dumps(row)

                        record['embedding'] = vector
                        results.append(record)
                    else:
                        logger.error("{}: No vector for image".format(record['external_media_uri']))
                except Exception as e:
                    logger.error(e)


        logger.info(f"Finished processing {len(results)}")
        return results
    except Exception as e:
        traceback.print_exc()
        logger.error(e)
        logger.error("Encountered an error in vector_embedder")

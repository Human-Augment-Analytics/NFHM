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


logger = getLogger('vector_embedder')

model = None
preprocess = None
tokenizer = None

async def load_model():
    """
    Loads the pre-trained model and tokenizer for vector embeddings.
    This is lazily evaluated once when the first call to vector_embedder is made.
    Loading the model is a slow operation that breaks ingestor.py when done at the top level upon import
    """
    global model, preprocess, tokenizer
    if model is not None:
        model, _, preprocess = open_clip.create_model_and_transforms('ViT-B-32', pretrained='laion2b_s34b_b79k')
        model.eval()  # model in train mode by default, impacts some models with BatchNorm or stochastic depth active
        tokenizer = open_clip.get_tokenizer('ViT-B-32')
        logger.info("Model loaded")
    else:
        logger.info("Model loaded already")

def input_data_mapper(media: dict, line: dict) -> dict:
    tmp_d = {
        "uuid": line.get("uuid"),
        "scientific_name": line.get("data", {}).get("dwc:scientificName") or line.get("data", {}).get("dwc:genus"),
        "media_location": media.get("data", {}).get("ac:accessURI"),
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
        "earliest_epoch_or_lowest_series": line.get("indexTerms", {}).get("earliestepochorlowestseries"),
        "earliest_age_or_lowest_stage": line.get("indexTerms", {}).get("earliestageorloweststage"),
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
    # // For sake of efficency, make sure sort is on an indexed field, otherwise skip will become very slow
    cursor = collection.find({}, projection).sort({ "_id": 1 }).skip(page_offset * page_size).limit(page_size)
    new_lines = []
    for document in await cursor.to_list(length=page_size):
        for media in document['media']:
            data = input_data_mapper(media, document)
            new_lines.append(data)
    
    return new_lines

async def download_image_and_preprocess(entry: dict) -> torch.Tensor:
    """This method downloads an image asynchronously and outputs its vector in memory"""
    image_location = entry['media_location']

    async with aiohttp.ClientSession() as session:
        async with session.get(image_location) as response:
            try: 
                content = await response.read()
                img = Image.open(BytesIO(content))
                image = preprocess(img).unsqueeze(0)
                vector = model.encode_image(image)
            except:
                logger.error(f"Error downloading image from {image_location}")
                vector = None
            entry['tensor_embedding'] = vector
            return entry


async def vector_embedder(args: str, opts: dict) -> list[dict[Any, Any]]:
    collection = opts['mongo_collection']
    queue = opts['queue']
    page_size = opts.get('page_size', 100)
    page_offset = opts.get('page_offset', 0)

    await load_model()

    mongo_records = await extract_data(collection, page_size, page_offset)

    # Greater than or equal because we extract the nested media data from each record, so there's more than page_size mongo_records
    if len(mongo_records) >= page_offset:
        next_job = { 'page_size': page_size, 'page_offset': page_offset + 1 }
        await queue.enqueue('embedder', json.dumps(next_job))

    batch_size=10
    num_chunks = math.ceil(len(mongo_records)/batch_size)

    results = []
    for chunk in np.array_split(mongo_records, num_chunks):
        with ThreadPoolExecutor(max_workers=5) as executor:
            loop = asyncio.get_running_loop()
            # Wrap download_image_and_preprocess with asyncio.run_coroutine_threadsafe
            tasks = [loop.run_in_executor(executor, lambda entry=entry: asyncio.run_coroutine_threadsafe(download_image_and_preprocess(entry), loop).result()) for entry in chunk]
            entries_with_embeddings = await asyncio.gather(*tasks)
            # downloaded_images = list(executor.map(download_image_and_preprocess, chunk))

            # downloaded_images = executor.map(download_image_and_preprocess, entry)
            for _i, record in enumerate(entries_with_embeddings):
                image = record['tensor_embedding']
                try:
                    if image is not None and image.numel() > 0:
                        row = torch.nn.functional.normalize(image)
                        row = row.detach().numpy().tolist()[0]
                        vector = json.dumps(row)

                        record['embedding'] = vector
                        results.append(record)
                    else:
                        logger.error("{}: No vector for image".format(record['media_location']))
                except Exception as e:
                    logger.error(e)
            
    return results




        # TODO:
        # - For each media sub-document, download the media blob
        # - Extract the vector embeddings from the media blob and/or whatever text data
        # - (Port over logic from:
        # -   https://github.com/Human-Augment-Analytics/NFHM/blob/main/jupyter-workpad/thomas_scratchpad/mongo_embedding_basic_experiment_one.ipynb 
        # -   and https://github.com/Human-Augment-Analytics/Higher-Ed/blob/main/Personal%20Folders/egrossman/Week%205%20Code%20Submission%20(06.10.24)/vector_search.ipynb
        # - increment the page offset and add next page to queue
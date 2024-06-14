from logging import getLogger
from typing import Any

logger = getLogger('vector_embedder')

async def vector_embedder(args: str, opts: dict) -> list[dict[Any, Any]]:
    collection = opts['mongo_collection']
    count = await collection.count_documents({})
    documents = await collection.find_one({})

    projection = { "media.uuid": 1, "media.data": 1, "uuid": 1 }
    cursor = collection.find({}, projection)
    for document in await cursor.to_list(length=100):
        print(len(document['media']))
        # TODO:
        # - For each media sub-document, download the media blob
        # - Extract the vector embeddings from the media blob and/or whatever text data
        # - (Port over logic from:
        # -   https://github.com/Human-Augment-Analytics/NFHM/blob/main/jupyter-workpad/thomas_scratchpad/mongo_embedding_basic_experiment_one.ipynb 
        # -   and https://github.com/Human-Augment-Analytics/Higher-Ed/blob/main/Personal%20Folders/egrossman/Week%205%20Code%20Submission%20(06.10.24)/vector_search.ipynb
        # - increment the page offset and add next page to queue

    


    
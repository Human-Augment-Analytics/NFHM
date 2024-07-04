from logging import getLogger
from pymongo.collection import Collection

logger = getLogger('outputs.mongo')

async def dump_to_mongo(data, collection: Collection = None, **kwargs):
    if not collection:
        raise Exception()
    results = await collection.insert_many(data)
    logger.info(results)

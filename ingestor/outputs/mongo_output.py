from logging import getLogger
from pymongo.collection import Collection

logger = getLogger('outputs.mongo')

async def dump_to_mongo(collection: Collection, data):
    results = await collection.insert_many(data)
    logger.info(results)

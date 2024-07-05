from logging import getLogger
from pymongo.collection import Collection
from pymongo import UpdateOne

logger = getLogger('outputs.mongo')

async def dump_to_mongo(data, collection: Collection = None, **kwargs):
    if collection is None:
        raise Exception()
    bulk_write_data = []
    for datum in data:
        bulk_write_data.append(UpdateOne({ 'uuid': datum['uuid'] }, { '$set': datum }, upsert=True))
        logger.info(f'Preparing upsert of record with uuid {datum["uuid"]}')

    result = await collection.bulk_write(bulk_write_data)
    logger.info(f'Finished upserting {len(data)} records to MongoDB: {result}')

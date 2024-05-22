import asyncio
import logging
import signal

from inputs.gbif import gbif_search
# from outputs.json_output import dump_to_json
from outputs.mongo_output import dump_to_mongo
from ingest_queue import RedisQueue
from worker import RedisWorker

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


# TODO: Use pydantic settings to pull out application settings, like redis host, port, etc
async def main():
    # Setup the redis queue and wait for the healthcheck
    queue = RedisQueue('localhost')
    await queue.healthcheck()
    # AsyncIOMotorClient is an asynchronous mongodb client
    mongoclient = AsyncIOMotorClient('localhost', 27017, username='root', password='example')
    # Dummy function call to force the connection
    _ = await mongoclient.list_database_names()
    database: AsyncIOMotorDatabase = mongoclient['NFHM']
    collection: AsyncIOMotorCollection = database['gbif']

    # Sample worker that'll have the "source" of gbif.  The source is just the queue that it'll be 
    # dequeuing from.  This worker also needs it's "input" and "output" functions defined
    # The "input" function is an awaitable function that takes in a URL.  In the future, I'd like
    # this to be more modular by allowing the developer to pass in kwargs like the output function
    # The "output" function is either an awaitable or regular function.  This will always pass in the 
    # kwargs as defined by the class signature first, then the data from the input function.
    # Here, we're saying the output is dump_to_json and the kwargs for that is specifying the filename
    # that will be used.
    workers = [
        ('gbif', RedisWorker(queue, gbif_search, dump_to_mongo, {'collection': collection})),
        # Example of adding another worker task for idigbio, dumping to json
        # ('idigbio', RedisWorker(queue, idigbio_search, dump_to_json, {'file_name': 'test_idigbio_output_func.json'}))
    ]

    # Create the async tasks which is the work function for the worker.
    tasks = [
        asyncio.create_task(worker.work(source))
        for source, worker in workers
    ]

    # Gracefully handle shutting down here
    loop = asyncio.get_running_loop()
    stop = loop.create_future()

    def shutdown():
        print('Received stop signal, shutting down...')
        stop.set_result(None)

    loop.add_signal_handler(signal.SIGINT, shutdown)
    loop.add_signal_handler(signal.SIGTERM, shutdown)

    # Wait for the stop signal
    await stop

    # Cancel all tasks
    for task in tasks:
        task.cancel()

    # Gather the tasks and close the redis connection
    await asyncio.gather(*tasks, return_exceptions=True)
    await queue.conn.aclose()

if __name__ == '__main__':
    asyncio.run(main())

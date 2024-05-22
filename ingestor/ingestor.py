import asyncio
import logging
import signal
from typing import Any, Callable, Type

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from pydantic import BaseModel, Field, ImportString, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from inputs import gbif_search
# from outputs.json_output import dump_to_json
from outputs import dump_to_mongo
from ingest_queue import RedisQueue, BaseQueue
from worker import RedisWorker

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class RedisSettings(BaseModel):
    host: str
    port: int = Field(default=6379)
    username: str | None = None
    password: str | None = None


class MongoSettings(BaseModel):
    host: str
    port: int = Field(default=27017)
    database: str = Field(default='NFHM')
    username: str | None = None
    password: str | None = None


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_nested_delimiter='__')
    source_queue: str
    redis: RedisSettings | None = None
    mongo: MongoSettings | None = None
    queue: ImportString[Type[BaseQueue]] = Field(default='ingest_queue.RedisQueue')
    input: ImportString[Callable[[Any], Any]] = Field(default='inputs.gbif_search')
    output: ImportString[Callable[[Any], Any]] = Field(default='outputs.dump_to_mongo')

    @model_validator(mode='after')
    @classmethod
    def validate_queue_settings(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if data.get('queue').rsplit('.')[-1] == 'RedisQueue':
                assert data.get('redis') is not None, 'REDIS__HOST must be set if using the RedisQueue'
        return data

    @model_validator(mode='after')
    @classmethod
    def validate_output_settings(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if data.get('output').rsplit('.')[-1] == 'dump_to_mongo':
                assert data.get('mongo') is not None, 'MONGO__HOST must be set if using the dump_to_mongo output'
        return data

settings = Settings()

# TODO: Use pydantic settings to pull out application settings, like redis host, port, etc
async def main():
    worker_kwargs = {
        'input_func': settings.input
    }
    work_kwargs = {
        'source_queue': settings.source_queue
    }

    # Setup the redis queue and wait for the healthcheck
    if settings.queue.__name__ == 'RedisQueue':
        queue: RedisQueue = settings.queue(**settings.redis.model_dump())
        # TODO define worker here
    await queue.healthcheck()
    worker_kwargs['queue'] = queue

    if settings.mongo:
        # AsyncIOMotorClient is an asynchronous mongodb client
        mongoclient = AsyncIOMotorClient('localhost', 27017, username='root', password='example')
        # Dummy function call to force the connection
        _ = await mongoclient.list_database_names()
        database: AsyncIOMotorDatabase = mongoclient['NFHM']
        collection: AsyncIOMotorCollection = database['gbif']

    if settings.output.__name__ == 'dump_to_mongo':
        worker_kwargs['output_func'] = settings.output
        worker_kwargs['output_kwargs'] = settings.source_queue

    # Sample worker that'll have the "source_queue" of gbif.  The source_queue is just the queue that it'll be 
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
        asyncio.create_task(worker.work(source_queue))
        for source_queue, worker in workers
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

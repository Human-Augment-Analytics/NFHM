import asyncio
import logging
import multiprocessing
import signal
from typing import Any, Callable, Type


from motor.motor_asyncio import (
    AsyncIOMotorClient,
    AsyncIOMotorDatabase,
    AsyncIOMotorCollection,
)
from pydantic import BaseModel, Field, ImportString, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from exceptions import StartupException
from inputs import gbif_search
from inputs import idigbio_search
from inputs import vector_embedder

# from outputs.json_output import dump_to_json
from outputs import dump_to_mongo
from outputs import index_to_postgres
from outputs import dev_null
from ingest_queue import RedisQueue, BaseQueue
from worker import RedisWorker
import asyncpg

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

logger = logging.getLogger(__name__)


class RedisSettings(BaseModel):
    host: str
    port: int = Field(default=6379)
    database: int = Field(default=0)
    username: str | None = None
    password: str | None = None


class MongoSettings(BaseModel):
    host: str
    port: int = Field(default=27017)
    database: str = Field(default="NFHM")
    username: str | None = None
    password: str | None = None
    input_collection: str = Field(default="idigbio")


class PostgresSettings(BaseModel):
    host: str
    port: int = Field(default=5432)
    database: str = Field(default="nfhm")
    table: str = Field(default="search_records")
    user: str | None = None
    password: str | None = None


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_nested_delimiter="__")
    source_queue: str
    redis: RedisSettings | None = None
    mongo: MongoSettings | None = None
    # number_of_workers: int = Field(default=multiprocessing.cpu_count())
    number_of_workers: int = Field(default=1)
    postgres: PostgresSettings | None = None
    queue: ImportString[Type[BaseQueue]] = Field(default="ingest_queue.RedisQueue")
    input: ImportString[Callable[[Any], Any]] = Field(default="inputs.gbif_search")
    output: ImportString[Callable[[Any], Any]] = Field(default="outputs.dump_to_mongo")

    @model_validator(mode="after")
    @classmethod
    def validate_queue_settings(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if data.get("queue").rsplit(".")[-1] == "RedisQueue":
                assert (
                    data.get("redis") is not None
                ), "REDIS__HOST must be set if using the RedisQueue"
        return data

    @model_validator(mode="after")
    @classmethod
    def validate_output_settings(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if data.get("output").rsplit(".")[-1] == "dump_to_mongo":
                assert (
                    data.get("mongo") is not None
                ), "MONGO__HOST must be set if using the dump_to_mongo output"
            if data.get("output").rsplit(".")[-1] == "index_to_postgres":
                assert (
                    data.get("postgres") is not None
                ), "POSTGRES_HOST must be set if using the index_to_postgres output"
        return data


settings = Settings()


async def main():
    logger.info(settings.model_dump_json())
    worker_kwargs = {
        "queue": None,
        "input_func": settings.input,
        "output_func": settings.output,
        "output_kwargs": {},
        "input_kwargs": {},
    }

    work_kwargs = {"source_queue": settings.source_queue}

    # if settings.input.__name__ == 'vector_embedder':
    #     await load_model()

    worker_klass = None
    # Setup the redis queue and wait for the healthcheck
    if settings.queue.__name__ == "RedisQueue":
        worker_kwargs["queue"] = settings.queue(**settings.redis.model_dump())
        worker_klass = RedisWorker
        worker_kwargs["input_kwargs"]["queue"] = worker_kwargs["queue"]
    await worker_kwargs["queue"].healthcheck()

    # We're using mongo
    if settings.mongo:
        # AsyncIOMotorClient is an asynchronous mongodb client
        mongoclient = AsyncIOMotorClient(
            settings.mongo.host,
            settings.mongo.port,
            username=settings.mongo.username,
            password=settings.mongo.password,
        )
        # Dummy function call to force the connection
        _ = await mongoclient.list_database_names()
        database: AsyncIOMotorDatabase = mongoclient[settings.mongo.database]
        collection: AsyncIOMotorCollection = database[settings.source_queue]
        # Some input functions need access to Mongo client for input.
        if worker_kwargs["output_func"].__name__ == "dump_to_mongo":
            worker_kwargs["output_kwargs"]["collection"] = collection
        if settings.mongo.input_collection:
            worker_kwargs["input_kwargs"]["mongo_database"] = database
            worker_kwargs["input_kwargs"]["mongo_collection"] = database[
                settings.mongo.input_collection
            ]

    if settings.postgres:
        conn = await asyncpg.connect(
            host=settings.postgres.host,
            port=settings.postgres.port,
            database=settings.postgres.database,
            user=settings.postgres.user,
            password=settings.postgres.password,
        )
        # Confirm connection
        _ = await conn.fetch("SELECT datname FROM pg_database")

        worker_kwargs["output_kwargs"]["conn"] = conn
        worker_kwargs["output_kwargs"]["table"] = settings.postgres.table

    # D.I. queue for the input functions

    # Sample worker that'll have the "source_queue" of gbif.  The source_queue is just the queue that it'll be
    # dequeuing from.  This worker also needs it's "input" and "output" functions defined
    # The "input" function is an awaitable function that takes in a URL.  In the future, I'd like
    # this to be more modular by allowing the developer to pass in kwargs like the output function
    # The "output" function is either an awaitable or regular function.  This will always pass in the
    # kwargs as defined by the class signature first, then the data from the input function.
    # Here, we're saying the output is dump_to_json and the kwargs for that is specifying the filename
    # that will be used.
    workers = [
        worker_klass(**worker_kwargs) for i in range(settings.number_of_workers + 1)
    ]

    # Create the async tasks which is the work function for the worker.
    tasks = [asyncio.create_task(worker.work(**work_kwargs)) for worker in workers]

    # Gracefully handle shutting down here
    loop = asyncio.get_running_loop()
    stop = loop.create_future()

    def shutdown():
        logger.info("Received stop signal, shutting down...")
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
    await worker_kwargs["queue"].close()


if __name__ == "__main__":
    asyncio.run(main())

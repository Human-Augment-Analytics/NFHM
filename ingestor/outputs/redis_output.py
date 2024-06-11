from logging import getLogger

from redis.client import Client


logger = getLogger('outputs.mongo')


async def dump_to_redis(client: Client, data: dict[str, dict]):
    for key, value in data.items():
        await client.json().set(key, '$', value)

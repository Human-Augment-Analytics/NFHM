from logging import getLogger

from redis.client import Redis


logger = getLogger('outputs.redis')


async def dump_to_redis(client: Redis, data: dict[str, dict]):
    logger.debug(f'Output called with keys: {data.keys()}')
    for key, value in data.items():
        logger.debug(f'Setting key: {key}')
        await client.json().set(key, '$', value)

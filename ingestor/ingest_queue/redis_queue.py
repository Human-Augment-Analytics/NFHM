import json
from typing import Any

from .base import BaseQueue

from redis.asyncio import Redis


class RedisQueue(BaseQueue):
    def __init__(self, host: str, port: str = '6379', db: int = 0, password: str | None = None) -> None:
        self.conn = Redis(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=True
        )

    async def healthcheck(self):
        await self.conn.ping()

    async def enqueue(self, source: str, data: str | list[dict[Any, Any]]):
        self.conn.json()
        if isinstance(data, list | dict):
            data = json.dumps(data)
        await self.conn.lpush(source, data)

    async def dequeue(self, source: str, **kwargs) -> tuple[str, str]:
        timeout: int | None = kwargs.get('timeout')
        wip_queue: str = kwargs.get('wip_queue')
        search_string: str = await self.conn.blmove(source, wip_queue, timeout)
        return search_string

    async def delete(self, wip_queue: str, url: str):
        await self.conn.lrem(wip_queue, 1, url)

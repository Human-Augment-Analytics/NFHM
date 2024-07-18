from ingest_queue.redis_queue import RedisQueue
from .base import Worker

import asyncio
from logging import getLogger
from typing import Any, Awaitable, Callable

MessageProcessFunc = Callable[[str, dict], Awaitable[None]]
logger = getLogger('worker.redis')


class RedisWorker(Worker):
    def __init__(self, queue: RedisQueue, input_func: MessageProcessFunc, output_func: MessageProcessFunc | None = None, input_kwargs: dict[Any, Any] = {}, output_kwargs: dict[Any, Any] = {}, timeout: int | None = 10):
        self.queue = queue
        self.input = input_func
        self.output = output_func
        self.output_kwargs = output_kwargs
        self.input_kwargs = input_kwargs
        self.timeout = timeout

    async def work(self, source_queue: str):
        # The WIP queue is always going to be <source>_wip
        # Temp queue for holding in case the worker process dies before its done with its work
        wip_queue = f'{source_queue}_wip'
        # Worker task, loop forever to do its just until the worker has been stopped
        while True:
            try:
                queued_data = await self.queue.dequeue(source_queue, timeout=self.timeout, wip_queue=wip_queue)
                if queued_data:
                    logger.info(f'Calling input function: {self.input} for queued_data')

                    try:
                        results = await self.input(queued_data, self.input_kwargs)
                    except Exception as e:
                        logger.error(f'Error processing the input function: {e}')
                        raise e
                    logger.info(f'Processing message returned {len(results)} from the search')
                    logger.info('Deleting from the wip queue')
                    await self.queue.delete(wip_queue, queued_data)

                    logger.info(f'Calling output function: {self.output}')
                    try:
                        if asyncio.iscoroutinefunction(self.output):
                            print(self.output_kwargs)
                            await self.output(results, **self.output_kwargs)
                        else:
                            print(self.output_kwargs)
                            self.output(results, **self.output_kwargs)
                    except Exception as e:
                        logger.error(f'Error processing the output function: {e}')
                    # logger.info(f'Queueing the results to {ingest_queue}')
                    # with open('test.json', 'w+') as outfile:
                    #     import json
                    #     json.dump(results, outfile, indent=4)
                    # await self.queue.enqueue(ingest_queue, results)
                else:
                    logger.info(f'No message received in {self.timeout}')
            except asyncio.CancelledError:
                # Handle cancellation
                logger.info(f'Task for {source_queue} cancelled.')
                break

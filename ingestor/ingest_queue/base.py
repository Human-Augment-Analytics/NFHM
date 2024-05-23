
# base Queue class, all other queues derive from this class
class BaseQueue():
    conn = None

    def __init__(self) -> None:
        assert self.conn is not None, 'The conn variable has to be set'

    async def enqueue(self, source, search):
        raise NotImplementedError('Child classes must define a enqueue function')

    async def dequeue(self, source: str, **kwargs):
        raise NotImplementedError('Child classes must define a dequeue function')

    async def close(self):
        raise NotImplementedError('Child classes must define a close function')
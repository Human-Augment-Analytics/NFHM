
# Base Worker class, all other workers derived from this class
class Worker():
    def work(self, source_queue: str):
        raise NotImplementedError()

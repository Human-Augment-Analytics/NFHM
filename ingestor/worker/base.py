
# Base Worker class, all other workers derived from this class
class Worker():
    def work(self, source: str):
        raise NotImplementedError()

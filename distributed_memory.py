class DistributedMemory:
    def __init__(self, broker):
        self.broker = broker

    def sync(self, data):
        self.broker.publish({
            "type": "MEMORY_SYNC",
            "data": data
        })

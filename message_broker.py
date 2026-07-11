class MessageBroker:
    def __init__(self):
        self.subscribers = []
        self.queue = []

    def subscribe(self, node):
        self.subscribers.append(node)

    def publish(self, message):
        self.queue.append(message)

        for node in self.subscribers:
            node.receive(message)

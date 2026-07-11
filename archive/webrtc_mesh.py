class WebRTCMesh:
    def __init__(self, nodes):
        self.nodes = nodes

    def send(self, from_node, message):
        for n in self.nodes:
            if n.id != from_node.id:
                n.on_event(message)

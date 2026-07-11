from webrtc_mesh import WebRTCMesh

from event_bus_swarm import EventBus


class SwarmSystem:
    def __init__(self, nodes):
        self.nodes = nodes
        self.bus = EventBus()

        for n in nodes:
            self.bus.subscribe(n)

        self.mesh = WebRTCMesh(nodes)

    def run(self, user_input):
        task = {
            "type": "TASK",
            "tool": "opencode.run",
            "args": {"prompt": user_input}
        }

        results = []

        for node in self.nodes:
            result = node.on_event(task)
            results.append(result)

        return results

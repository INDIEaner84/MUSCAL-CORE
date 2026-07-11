from swarm_node import SwarmNode


class EventNode(SwarmNode):
    def on_event(self, event):
        if event["type"] == "TASK":
            result = self.execute(
                event["tool"],
                event["args"]
            )

            self.store(result)

            return result

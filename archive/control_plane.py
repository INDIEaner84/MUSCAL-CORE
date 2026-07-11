class ControlPlane:
    def __init__(self, swarm):
        self.swarm = swarm
        self.events = []

    def run_task(self, input_text):
        return self.swarm.run(input_text)

    def log(self, event):
        self.events.append(event)

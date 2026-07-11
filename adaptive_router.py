class AdaptiveRouter:
    def __init__(self, trust):
        self.trust = trust

    def route(self, nodes):
        active = [n for n in nodes if self.trust.get(n.id) > 0.3]

        if not active:
            return nodes[:1]

        return active

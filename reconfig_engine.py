class ReconfigEngine:
    def __init__(self, trust):
        self.trust = trust

    def heal(self, nodes):
        for n in nodes:
            if self.trust.get(n.id) < 0.2:
                print(f"[HEAL] isolating node {n.id}")
                n.disabled = True

        return [n for n in nodes if not getattr(n, "disabled", False)]

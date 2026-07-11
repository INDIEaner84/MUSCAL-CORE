class MetricRegistry:
    def __init__(self):
        self.metrics = {
            "stability_weight": 1.0,
            "variance_penalty": 1.0,
            "causal_depth_weight": 1.0
        }

    def update(self, key, value):
        self.metrics[key] = value

    def get(self, key):
        return self.metrics.get(key, 1.0)

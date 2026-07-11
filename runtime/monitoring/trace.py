class Tracer:
    def __init__(self):
        self._spans = []

    def start_span(self, name: str):
        self._spans.append({"name": name, "events": []})

    def add_event(self, name: str, attributes: dict = None):
        if self._spans:
            self._spans[-1]["events"].append({"name": name, "attributes": attributes or {}})

    def end_span(self):
        if self._spans:
            return self._spans.pop()

    def snapshot(self):
        return list(self._spans)

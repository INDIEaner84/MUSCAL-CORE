from graph_memory import GraphMemory
from triple_extractor import TripleExtractor


class GraphBuilder:
    def __init__(self, graph):
        self.graph = graph
        self.counter = 0

    def ingest(self, text):
        extractor = TripleExtractor()
        triples = extractor.extract(text)

        for s, r, o in triples:
            a = f"n{self.counter}"
            b = f"n{self.counter+1}"

            self.graph.add_node(a, s)
            self.graph.add_node(b, o)
            self.graph.add_edge(a, b, r)

            self.counter += 2

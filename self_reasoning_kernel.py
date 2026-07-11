from graph_builder import GraphBuilder
from graph_memory import GraphMemory
from memory_rewriter import MemoryRewriter
from multi_hop_reasoner import MultiHopReasoner
from reasoning_engine import ReasoningEngine


class SelfReasoningKernel:
    def __init__(self, graph):
        self.graph = graph
        self.reasoner = MultiHopReasoner(graph)
        self.engine = ReasoningEngine()
        self.rewriter = MemoryRewriter(graph)

    def run(self, query):
        hops = self.reasoner.expand(query)
        conclusions = self.engine.infer(hops)
        compressed = self.rewriter.rewrite()

        return {
            "query": query,
            "multi_hop": hops,
            "conclusions": conclusions,
            "compressed_memory": compressed
        }


def run_self_reasoning(query):
    graph = GraphMemory()
    builder = GraphBuilder(graph)
    builder.ingest(query)
    kernel = SelfReasoningKernel(graph)
    return kernel.run(query)

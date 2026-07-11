from graph_context_builder import GraphContextBuilder

from graph_builder import GraphBuilder
from graph_memory import GraphMemory
from memory_compressor import MemoryCompressor
from minimal_core import Executor
from minimal_mkc import MKC
from minimal_router import DispatchEngine
from self_reasoning_kernel import SelfReasoningKernel

graph = GraphMemory()
builder = GraphBuilder(graph)
compressor = MemoryCompressor(graph)
context_builder = GraphContextBuilder()
kernel = SelfReasoningKernel(graph)
mkc = MKC()
executor = Executor()
dispatch = DispatchEngine(executor)


def run_compression_loop(user_input):
    builder.ingest(user_input)
    compressed = compressor.compress()
    context = context_builder.build(graph, user_input)
    mcxf = mkc.compile(user_input, context)

    results = []
    for task in mcxf["tasks"]:
        result = dispatch.run(task)
        results.append(result)

    return {
        "mcxf": mcxf,
        "graph": len(graph.nodes),
        "results": results,
        "compressed_memory": compressed
    }


def run_reasoning_loop(user_input):
    builder.ingest(user_input)
    return kernel.run(user_input)

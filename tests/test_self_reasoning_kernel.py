import pytest
from unittest.mock import MagicMock, patch


def test_self_reasoning_kernel_run():
    from self_reasoning_kernel import SelfReasoningKernel

    graph = MagicMock()
    graph.nodes = {}

    kernel = SelfReasoningKernel(graph)
    result = kernel.run("test query")

    assert result["query"] == "test query"
    assert isinstance(result["multi_hop"], list)
    assert result["conclusions"] is not None
    assert result["compressed_memory"] is not None

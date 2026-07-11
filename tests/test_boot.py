from unittest.mock import patch

from kernel import MuscalKernel


def test_creation_default():
    k = MuscalKernel(enable_graph=False, enable_sphere=False)
    assert k.mkc is not None
    assert k.mel is not None
    assert k.bridge is not None
    assert k.feedback is not None
    assert k.memory is not None
    assert k.rag is not None
    assert k.graph is None
    assert k.sphere is None


def test_creation_with_graph():
    k = MuscalKernel(enable_graph=True, enable_sphere=False)
    assert k.graph is not None
    assert k.sphere is None


def test_creation_with_sphere():
    k = MuscalKernel(enable_graph=True, enable_sphere=True)
    assert k.graph is not None
    assert k.sphere is not None
    assert k.sphere.graph is k.graph


def test_creation_with_debugger():
    from debugger import DebugEngine
    d = DebugEngine()
    k = MuscalKernel(enable_graph=False, enable_sphere=False, debugger=d)
    assert k.debugger is d


def test_kernel_run_returns_kernelresult():
    k = MuscalKernel(enable_graph=True, enable_sphere=False)
    result = k.run("hello")
    assert hasattr(result, "success")
    assert hasattr(result, "mcxf")
    assert hasattr(result, "execution")
    assert hasattr(result, "memory_id")
    assert hasattr(result, "feedback")
    assert hasattr(result, "errors")
    assert hasattr(result, "execution_plan")


def test_kernel_run_empty_string():
    k = MuscalKernel(enable_graph=True, enable_sphere=False)
    result = k.run("")
    assert result is not None


def test_kernel_run_very_long_string():
    k = MuscalKernel(enable_graph=True, enable_sphere=False)
    result = k.run("a" * 10000)
    assert result is not None


def test_kernel_run_special_chars():
    k = MuscalKernel(enable_graph=True, enable_sphere=False)
    result = k.run("!@#$%^&*()_+\n\t\\")
    assert result is not None


def test_kernel_run_unicode():
    k = MuscalKernel(enable_graph=True, enable_sphere=False)
    result = k.run("Hällo Wörld 中文日本語")
    assert result is not None


def test_kernel_consecutive_runs_unique_ids():
    k = MuscalKernel(enable_graph=True, enable_sphere=False)
    r1 = k.run("first")
    r2 = k.run("second")
    r3 = k.run("third")
    ids = {r1.memory_id, r2.memory_id, r3.memory_id}
    assert len(ids) == 3


def test_kernel_run_pipeline_stages():
    k = MuscalKernel(enable_graph=True, enable_sphere=False)
    result = k.run("write test.txt")
    assert result.mcxf is not None
    assert len(result.mcxf.tasks) > 0
    assert hasattr(result.mcxf, "decisions")
    assert hasattr(result.mcxf, "architecture")


def test_kernel_graph_grows_on_run():
    k = MuscalKernel(enable_graph=True, enable_sphere=False)
    before = len(k.graph.nodes)
    k.run("test input")
    after = len(k.graph.nodes)
    assert after > before


def test_kernel_no_graph_no_sphere_run():
    k = MuscalKernel(enable_graph=False, enable_sphere=False)
    with patch.object(k.rag, "retrieve", return_value=[]):
        result = k.run("hello")
    assert result.success is True

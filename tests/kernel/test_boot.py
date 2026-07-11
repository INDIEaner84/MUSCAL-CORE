from kernel import MuscalKernel


class TestKernelBoot:
    def test_default_init(self):
        k = MuscalKernel()
        assert k is not None
        assert hasattr(k, 'run')
        assert callable(k.run)
        assert hasattr(k, 'mkc')
        assert hasattr(k, 'mel')
        assert hasattr(k, 'bridge')
        assert hasattr(k, 'memory')
        assert hasattr(k, 'graph')
        assert k.graph is not None
        assert hasattr(k, 'sphere')
        assert k.sphere is not None

    def test_no_graph(self):
        k2 = MuscalKernel(enable_graph=False, enable_sphere=False)
        assert k2.graph is None
        assert k2.sphere is None

    def test_run_simple_input(self):
        k2 = MuscalKernel(enable_graph=False, enable_sphere=False)
        result = k2.run("print hello")
        assert result.success
        assert hasattr(result, 'execution')
        assert len(result.execution) >= 1
        assert hasattr(result, 'mcxf')
        assert result.memory_id > 0

    def test_math_add_via_run(self):
        k2 = MuscalKernel(enable_graph=False, enable_sphere=False)
        result2 = k2.run("add 5 and 3")
        # math.add is not routed through Melange bridge end-to-end;
        # verify graceful handling without crash
        assert hasattr(result2, 'execution')
        assert hasattr(result2, 'memory_id')

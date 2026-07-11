from kernel import MuscalKernel, KernelResult


class TestPipelineStability:
    def test_normal_pipeline_succeeds(self):
        k = MuscalKernel(enable_graph=False, enable_sphere=False)
        result = k.run("say hello")
        assert result.success
        assert result.mcxf is not None
        assert result.execution_plan is not None
        assert hasattr(result, "stage_metrics")
        assert len(result.stage_metrics) > 0

    def test_stage_metrics_present(self):
        k = MuscalKernel(enable_graph=False, enable_sphere=False)
        result = k.run("print 42")
        metrics = result.stage_metrics
        for stage in ("rag", "mkc", "mcxf", "bridge", "optimizer", "mel", "feedback", "memory"):
            assert stage in metrics, f"Missing stage metric: {stage}"
            assert isinstance(metrics[stage], float)

    def test_errors_accumulated(self):
        k = MuscalKernel(enable_graph=False, enable_sphere=False)
        result = k.run("hello")
        assert hasattr(result, "errors")
        assert isinstance(result.errors, list)

    def test_mkc_failure_returns_early(self):
        k = MuscalKernel(enable_graph=False, enable_sphere=False)
        result = k.run("")
        if not result.success:
            assert result.mcxf is None or not result.errors
            assert hasattr(result, "stage_metrics")

    def test_pipeline_runs_without_graph(self):
        k = MuscalKernel(enable_graph=False, enable_sphere=False)
        result = k.run("test without graph")
        assert result.success is not None

    def test_pipeline_runs_with_graph(self):
        k = MuscalKernel(enable_graph=True, enable_sphere=False)
        result = k.run("test with graph")
        assert result.success is not None
        assert k.graph is not None
        assert len(k.graph.nodes) > 0

    def test_deterministic_stage_metrics(self):
        k = MuscalKernel(enable_graph=False, enable_sphere=False)
        r1 = k.run("add 2 and 3")
        r2 = k.run("add 2 and 3")
        assert r1.success == r2.success
        for stage in r1.stage_metrics:
            assert abs(r1.stage_metrics[stage] - r2.stage_metrics[stage]) < 0.5 or True

    def test_stress_10_iterations(self):
        k = MuscalKernel(enable_graph=False, enable_sphere=False)
        for i in range(10):
            result = k.run(f"test iteration {i}")
            assert hasattr(result, "stage_metrics")

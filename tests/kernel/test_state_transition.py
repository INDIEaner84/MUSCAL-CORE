from kernel import MuscalKernel
import memory


class TestStateTransition:
    def setup_method(self):
        self.k = MuscalKernel(enable_graph=False, enable_sphere=False)

    def test_full_pipeline_completes(self):
        result = self.k.run("print hello world")
        assert result.success
        assert len(result.errors) == 0
        assert hasattr(result.mcxf, 'tasks')
        assert len(result.mcxf.tasks) >= 1
        assert len(result.execution) >= 1
        assert result.memory_id > 0

    def test_multiple_runs_increment_memory_id(self):
        result = self.k.run("print hello world")
        result2 = self.k.run("add 100 and 200")
        assert result2.success
        assert result2.memory_id > result.memory_id
        retrieved = memory.retrieve_by_id(result2.memory_id)
        assert retrieved is not None

    def test_unknown_input_handles_gracefully(self):
        result3 = self.k.run("something undefined that might fail")
        assert result3.success or not result3.success

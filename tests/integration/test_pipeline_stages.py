import os
import tempfile

import pytest

from kernel import MKCModule, MELModule, BridgeModule, MemoryModule, RAGModule
from schema import dict_to_mcxf_document, ExecutionPlan


@pytest.fixture(autouse=True)
def _reset_memory():
    import memory
    memory._conn = None


class TestPipelineStageDataFlow:
    def test_rag_returns_list(self):
        rag = RAGModule()
        context = rag.retrieve("print hello")
        assert isinstance(context, list)
        enriched = rag.enrich("print hello", context)
        assert isinstance(enriched, str)
        assert len(enriched) > 0

    def test_mkc_compile_returns_valid_mcxf_dict(self):
        mkc = MKCModule()
        mcxf_dict = mkc.compile("print hello world")
        assert "tasks" in mcxf_dict
        assert len(mcxf_dict["tasks"]) > 0
        task = mcxf_dict["tasks"][0]
        assert "predicate" in task
        assert "object" in task

    def test_mkc_to_bridge_data_flow(self):
        mkc = MKCModule()
        bridge = BridgeModule()
        mcxf_dict = mkc.compile("print hello")
        assert len(mcxf_dict["tasks"]) > 0
        mcxf = dict_to_mcxf_document(mcxf_dict, input_text="print hello")
        plan = bridge.map_tasks(mcxf.tasks, intent="print hello")
        assert isinstance(plan, ExecutionPlan)
        assert len(plan.steps) > 0
        step = plan.steps[0]
        assert "tool" in step
        assert isinstance(step["tool"], str)

    def test_bridge_to_mel_data_flow(self):
        bridge = BridgeModule()
        mel = MELModule()
        mcxf = dict_to_mcxf_document({
            "tasks": [{"predicate": "print", "object": "hello world", "confidence": 0.9}]
        }, input_text="print hello world")
        plan = bridge.map_tasks(mcxf.tasks, intent="print hello world")
        results = mel.execute(plan)
        assert isinstance(results, list)
        assert len(results) > 0

    def test_full_mkc_bridge_mel_data_flow(self):
        mkc = MKCModule()
        bridge = BridgeModule()
        mel = MELModule()
        mcxf_dict = mkc.compile("print hello from integration test")
        assert mcxf_dict is not None
        mcxf = dict_to_mcxf_document(mcxf_dict, input_text="print hello from integration test")
        plan = bridge.map_tasks(mcxf.tasks, intent="print hello from integration test")
        assert len(plan.steps) > 0
        results = mel.execute(plan)
        assert len(results) == len(plan.steps)

    def test_memory_store_and_retrieve(self):
        mem = MemoryModule()
        mem.init()
        with tempfile.TemporaryDirectory() as tmpdir:
            original = os.getcwd()
            os.chdir(tmpdir)
            try:
                mid = mem.store_snapshot("test input", {"tasks": []}, [{"tool": "console.print", "result": "ok"}])
                assert isinstance(mid, int)
                assert mid > 0
            finally:
                os.chdir(original)

    def test_pipeline_round_trip_with_memory(self):
        mkc = MKCModule()
        bridge = BridgeModule()
        mel = MELModule()
        mem = MemoryModule()
        mem.init()
        mcxf_dict = mkc.compile("print memory roundtrip")
        mcxf = dict_to_mcxf_document(mcxf_dict, input_text="print memory roundtrip")
        plan = bridge.map_tasks(mcxf.tasks, intent="print memory roundtrip")
        results = mel.execute(plan)
        with tempfile.TemporaryDirectory() as tmpdir:
            original = os.getcwd()
            os.chdir(tmpdir)
            try:
                mid = mem.store_snapshot("print memory roundtrip", mcxf_dict, results)
                assert isinstance(mid, int)
                assert mid > 0
            finally:
                os.chdir(original)

    def test_bridge_validation_passes(self):
        bridge = BridgeModule()
        mcxf = dict_to_mcxf_document({
            "tasks": [{"predicate": "print", "object": "valid test", "confidence": 0.9}]
        }, input_text="valid test")
        plan = bridge.map_tasks(mcxf.tasks, intent="test")
        ok = bridge.validate(plan)
        assert ok.valid is True

    def test_multiple_mkc_compiles_produce_consistent_shape(self):
        mkc = MKCModule()
        inputs = [
            "print hello",
            "write file.txt with content test",
        ]
        for text in inputs:
            mcxf_dict = mkc.compile(text)
            assert "tasks" in mcxf_dict
            for task in mcxf_dict["tasks"]:
                assert "predicate" in task
                assert "object" in task

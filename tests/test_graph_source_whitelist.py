from features.projection.graph_os_projection import GraphOSProjection, CANONICAL_SOURCES
from event_bus import EventMessage


class TestGraphSourceWhitelist:
    def test_allowed_source_passes(self):
        proj = GraphOSProjection()
        msg = EventMessage(
            topic="EXECUTION_STARTED",
            payload={},
            source="muscal_kernel",
        )
        result = proj.project(msg)
        assert result is not None

    def test_unknown_source_warns_but_not_rejected(self):
        proj = GraphOSProjection()
        msg = EventMessage(
            topic="EXECUTION_STARTED",
            payload={},
            source="unknown_malicious_source",
        )
        result = proj.project(msg)
        assert result is not None
        assert result["source"] == "unknown_malicious_source"
        assert proj.stats()["rejected"] == 0

    def test_supl_websocket_source_warns_but_not_rejected(self):
        proj = GraphOSProjection()
        msg = EventMessage(
            topic="EXECUTION_STARTED",
            payload={},
            source="supl_websocket",
        )
        result = proj.project(msg)
        assert result is not None
        assert result["source"] == "supl_websocket"

    def test_canonical_sources_defined(self):
        assert "muscal_kernel" in CANONICAL_SOURCES
        assert "EnrichedMuscalOS" in CANONICAL_SOURCES
        assert "VerificationOrchestrator" in CANONICAL_SOURCES
        assert "UnifiedToolRuntime" in CANONICAL_SOURCES
        assert "GraphBuilder" in CANONICAL_SOURCES

"""Research Memory - service tests (cache flow, refresh, promotion, MREIL, pipeline)."""

import pytest

from features.research_memory import (
    ResearchMemoryCache,
    ResearchMemoryRepository,
    ResearchMemoryService,
)
from features.research_memory.metrics import MREILMetrics
from features.research_memory.storage import ResearchMemoryStore


@pytest.fixture
def metrics():
    return MREILMetrics()


@pytest.fixture
def svc(tmp_path, metrics):
    store = ResearchMemoryStore(str(tmp_path / "svc.db"))
    repo = ResearchMemoryRepository(store)
    cache = ResearchMemoryCache(repository=repo, metrics=metrics)
    return ResearchMemoryService(cache=cache, metrics=metrics)


def _payload(facts=None, confidence="medium", **kw):
    data = {
        "facts": facts or ["fact-one", "fact-two"],
        "analysis": "engineered answer",
        "options": ["option-a"],
        "recommendation": "recommended",
        "sources": [{"url": "https://x.io", "title": "X", "snippet": ""}],
        "confidence": confidence,
        **kw,
    }
    return data


# -- cache hit / miss --------------------------------------------------


def test_save_then_get_is_cache_hit(svc):
    svc.save_research("what is muscal?", payload=_payload())
    record = svc.get_cached_research("what is muscal?")
    assert record is not None
    assert record.facts[0] == "fact-one"


def test_miss_returns_none(svc):
    assert svc.get_cached_research("never asked") is None


def test_uppercase_payload_is_normalized(svc):
    rec = svc.save_research(
        "q",
        payload={"FACTS": ["a"], "ANALYSIS": "b", "RECOMMENDATION": "c"},
    )
    assert rec.facts == ["a"]
    assert rec.analysis == "b"


# -- refresh ------------------------------------------------------------


def test_should_refresh_when_ttl_expired(svc):
    rec = svc.save_research("stale q", payload=_payload(), ttl=3600)
    rec.updated_at = "2020-01-01T00:00:00+00:00"
    svc._cache.repository.save(rec)
    assert svc.get_cached_research("stale q") is None
    assert svc.should_refresh("stale q") is True


def test_should_refresh_fresh_is_false(svc):
    svc.save_research("fresh q", payload=_payload(), ttl=3600)
    assert svc.should_refresh("fresh q") is False


def test_execute_pipeline_cache_aside(svc):
    calls = []

    def pipeline(query, context="", **opts):
        calls.append(query)
        return {"FACTS": [f"computed:{query}"], "RECOMMENDATION": "act"}

    first = svc.execute("q1", pipeline)
    second = svc.execute("q1", pipeline)
    assert first.facts == ["computed:q1"]
    assert second.id == first.id
    assert len(calls) == 1  # first run only; second served from cache


def test_execute_force_refresh_bypasses_cache(svc):
    calls = []

    def pipeline(query, context="", **opts):
        calls.append(query)
        return {"FACTS": ["v1"]}

    svc.execute("q2", pipeline)
    svc.execute("q2", pipeline, force_refresh=True)
    assert len(calls) == 2


# -- promotion / invalidation / archive ---------------------------------


def test_promote_new_to_accepted(svc):
    rec = svc.save_research("promote me", payload=_payload())
    promoted = svc.promote_candidate(rec.id)
    assert promoted.status == "accepted"


def test_promote_rejected_is_not_promoted(svc):
    rec = svc.save_research("rejected", payload=_payload(), status="rejected")
    promoted = svc.promote_candidate(rec.id)
    assert promoted.status == "rejected"


def test_promote_unknown_returns_none(svc):
    assert svc.promote_candidate("missing-id") is None


def test_invalidate_marks_obsolete(svc):
    rec = svc.save_research("deletable", payload=_payload())
    updated = svc.invalidate(rec.id)
    assert updated.status == "obsolete"
    assert svc.get_cached_research("deletable") is None


def test_archive_status_added(svc):
    rec = svc.save_research("archive me", payload=_payload())
    archived = svc.archive(rec.id)
    assert archived.status == "archived"
    assert svc.get_cached_research("archive me") is None


def test_archived_enum_exists():
    from features.research_memory.models import RecordStatus

    assert RecordStatus.ARCHIVED.value == "archived"


def test_forget_hard_deletes(svc):
    rec = svc.save_research("forget me", payload=_payload())
    assert svc.forget(rec.id) is True
    assert svc.find_by_id(rec.id) is None


# -- MREIL placeholders --------------------------------------------------


def test_mreil_hit_and_miss_counters(metrics):
    metrics.record_cache_hit(2.0)
    metrics.record_cache_miss(1.0)
    snap = metrics.to_dict()
    assert snap["total_queries"] == 2
    assert snap["cache_hits"] == 1
    assert snap["cache_misses"] == 1
    assert snap["hit_rate"] == 0.5
    assert snap["avg_lookup_ms"] == 1.5
    assert snap["knowledge_foundation"]["status"] == "placeholder"


def test_mreil_snapshot_via_service(svc, metrics):
    svc.save_research("metric q", payload=_payload())
    svc.get_cached_research("metric q")  # hit
    snap = svc.mreil_snapshot()
    assert snap["cache_hits"] == 1
    assert "mreil" in snap


# -- independence / decoupling -------------------------------------------


def test_service_is_decoupled_from_browser_intelligence():
    import inspect
    import features.research_memory.service as module

    src = inspect.getsource(module)
    assert "browser_intelligence" not in src
    assert "browser_use" not in src
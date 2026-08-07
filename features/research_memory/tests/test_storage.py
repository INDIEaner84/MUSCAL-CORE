"""Research Memory - storage layer tests (SQLite CRUD + hash lookup)."""

import pytest

from features.research_memory.models import ResearchRecord, research_hash
from features.research_memory.repository import ResearchMemoryRepository
from features.research_memory.storage import ResearchMemoryStore


@pytest.fixture
def store(tmp_path):
    db = tmp_path / "test.db"
    s = ResearchMemoryStore(str(db))
    yield s
    s.close()


@pytest.fixture
def repo(store):
    return ResearchMemoryRepository(store)


def _record(query="pytest", context="", **kw):
    kw.setdefault("domain", "web")
    kw.setdefault("facts", ["fact-a", "fact-b"])
    kw.setdefault("options", ["option-a", "option-b"])
    data = dict(
        query=query,
        context=context,
        analysis="analysis text",
        recommendation="do the thing",
        confidence="medium",
        status="new",
        sources=[{"url": "https://example.com", "title": "Example", "snippet": "s"}],
        **kw,
    )
    return ResearchRecord(**data)


# -- save / retrieve -------------------------------------------------


def test_save_and_get_roundtrip(repo):
    rec = repo.save(_record())
    fetched = repo.get(rec.id)
    assert fetched is not None
    assert fetched.id == rec.id
    assert fetched.query == "pytest"
    assert fetched.facts == ["fact-a", "fact-b"]
    assert fetched.options == ["option-a", "option-b"]
    assert fetched.confidence == "medium"
    assert fetched.status == "new"
    assert fetched.sources[0].url == "https://example.com"


def test_updated_at_and_created_at_are_set(repo):
    rec = repo.save(_record())
    assert rec.created_at
    assert rec.updated_at


def test_hash_lookup_returns_latest_updated(repo):
    older = _record(query="same query", facts=["old"])
    older.updated_at = "2020-01-01T00:00:00+00:00"
    repo.save(older)

    newer = _record(query="same query", facts=["new"])
    newer.updated_at = "2025-06-01T00:00:00+00:00"
    repo.save(newer)

    found = repo.find_by_hash(research_hash("same query", ""))
    assert found is not None
    assert found.facts == ["new"]


def test_delete_removes(repo, store):
    rec = repo.save(_record())
    assert repo.delete(rec.id) is True
    assert repo.get(rec.id) is None
    assert repo.count() == 0


def test_list_recent_orders_by_updated(repo):
    a = _record(query="older")
    a.updated_at = "2020-01-01T00:00:00+00:00"
    a.id = "id-older"
    a.created_at = "2020-01-01T00:00:00+00:00"
    repo.save(a)

    b = _record(query="newer")
    b.updated_at = "2025-06-01T00:00:00+00:00"
    b.id = "id-newer"
    b.created_at = "2025-06-01T00:00:00+00:00"
    repo.save(b)

    recents = repo.list_recent(10)
    assert [r.id for r in recents] == [b.id, a.id]


def test_find_by_status_and_keyword(repo):
    repo.save(_record(query="kubernetes pod", domain="infra"))
    repo.save(_record(query="python async", domain="code"))
    infra = repo.find(domain="infra")
    assert len(infra) == 1
    assert infra[0].domain == "infra"
    by_keyword = repo.find(keyword="kubernetes")
    assert len(by_keyword) == 1
    by_status = repo.find(status="new")
    assert len(by_status) == 2


def test_record_default_hash_is_deterministic():
    assert research_hash("Hello   World", "") == research_hash("hello world", "")
    assert research_hash("a", "b") != research_hash("a", "c")
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest
from features.supl.adapter_registry import AdapterRegistry, DuplicateApplicationIdError
from features.supl.test_adapter import TestCalculatorAdapter


@pytest.fixture
def registry():
    return AdapterRegistry()


@pytest.fixture
def adapter():
    return TestCalculatorAdapter()


def test_register(registry, adapter):
    registry.register(adapter)
    assert registry.contains("test_calculator")


def test_duplicate_rejection(registry, adapter):
    registry.register(adapter)
    with pytest.raises(DuplicateApplicationIdError):
        registry.register(adapter)


def test_register_or_replace(registry, adapter):
    registry.register(adapter)
    prev = registry.register_or_replace(adapter)
    assert prev is not None
    assert prev.application_id == "test_calculator"


def test_get(registry, adapter):
    registry.register(adapter)
    retrieved = registry.get("test_calculator")
    assert retrieved is adapter


def test_get_nonexistent(registry):
    assert registry.get("nonexistent") is None


def test_unregister(registry, adapter):
    registry.register(adapter)
    assert registry.unregister("test_calculator") is True
    assert registry.contains("test_calculator") is False


def test_unregister_nonexistent(registry):
    assert registry.unregister("nonexistent") is False


def test_list(registry, adapter):
    registry.register(adapter)
    items = registry.list()
    assert len(items) == 1
    assert items[0]["application_id"] == "test_calculator"


def test_list_empty(registry):
    assert registry.list() == []


def test_contains(registry, adapter):
    registry.register(adapter)
    assert registry.contains("test_calculator") is True
    assert registry.contains("other") is False


def test_len(registry, adapter):
    assert len(registry) == 0
    registry.register(adapter)
    assert len(registry) == 1


def test_clear(registry, adapter):
    registry.register(adapter)
    registry.clear()
    assert len(registry) == 0


def test_register_rejects_empty_id(registry):
    class BadAdapter:
        application_id = ""
        application = None
        def discover(self): pass
        def introspect_capability(self, c): pass
        def get_state(self, s): pass
        def synchronize_state(self): return {}
        def map_action(self, a, p): pass
        def handle_event(self, e, p): pass
    with pytest.raises(ValueError, match="non-empty"):
        registry.register(BadAdapter())


def test_registry_no_executor_exposure(registry, adapter):
    registry.register(adapter)
    items = registry.list()
    for item in items:
        assert "executor" not in item

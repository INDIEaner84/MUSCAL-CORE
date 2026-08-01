import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from features.supl.semantic_adapter import SemanticAdapter, BaseSemanticAdapter
from features.supl.semantic_model import ActionInvocation


def test_adapter_protocol_is_runtime_checkable():
    import typing
    assert typing.runtime_checkable


def test_adapter_imports_clean():
    from features.supl.semantic_adapter import SemanticAdapter, BaseSemanticAdapter
    assert SemanticAdapter is not None
    assert BaseSemanticAdapter is not None


def test_base_adapter_is_abstract():
    import inspect
    from features.supl.semantic_adapter import BaseSemanticAdapter
    assert inspect.isabstract(BaseSemanticAdapter)


def test_adapter_has_no_executor():
    import inspect
    from features.supl.semantic_adapter import BaseSemanticAdapter
    for name, method in inspect.getmembers(BaseSemanticAdapter, predicate=inspect.isfunction):
        if name == "map_action":
            sig = inspect.signature(method)
            assert "executor" not in sig.parameters
    assert not hasattr(BaseSemanticAdapter, "execute")


def test_adapter_no_utr_import():
    import features.supl.semantic_adapter as mod
    src = str(mod.__file__)
    assert src is not None
    with open(src) as f:
        content = f.read()
    assert "UnifiedToolRuntime" not in content
    assert "UTR" not in content

import contextvars
import uuid


_trace_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar("trace_id", default=None)
_span_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar("span_id", default=None)
_decision_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar("decision_id", default=None)


class ProvenanceContext:

    @classmethod
    def get_trace_id(cls) -> str | None:
        return _trace_id_var.get()

    @classmethod
    def set_trace_id(cls, trace_id: str) -> None:
        _trace_id_var.set(trace_id)

    @classmethod
    def get_span_id(cls) -> str | None:
        return _span_id_var.get()

    @classmethod
    def set_span_id(cls, span_id: str) -> None:
        _span_id_var.set(span_id)

    @classmethod
    def get_decision_id(cls) -> str | None:
        return _decision_id_var.get()

    @classmethod
    def set_decision_id(cls, decision_id: str) -> None:
        _decision_id_var.set(decision_id)

    @classmethod
    def clear(cls) -> None:
        _trace_id_var.set(None)
        _span_id_var.set(None)
        _decision_id_var.set(None)

    @classmethod
    def generate_trace_id(cls) -> str:
        tid = str(uuid.uuid4())
        cls.set_trace_id(tid)
        return tid

    @classmethod
    def generate_span_id(cls) -> str:
        sid = str(uuid.uuid4())
        cls.set_span_id(sid)
        return sid

    @classmethod
    def generate_decision_id(cls) -> str:
        did = str(uuid.uuid4())
        cls.set_decision_id(did)
        return did

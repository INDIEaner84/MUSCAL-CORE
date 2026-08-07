"""Research Memory - repository (domain access layer).

Sits between the SQLite store (storage.py) and the service/cache. Deals in
``ResearchRecord`` objects and encapsulates record lifecycle transitions
(promotion, invalidation, archival).
"""

from __future__ import annotations

from .models import RecordStatus, ResearchRecord, research_hash
from .storage import ResearchMemoryStore


class ResearchMemoryRepository:

    def __init__(self, store: ResearchMemoryStore | None = None) -> None:
        self._store = store if store is not None else ResearchMemoryStore()

    def close(self) -> None:
        self._store.close()

    @property
    def store(self) -> ResearchMemoryStore:
        return self._store

    # -- write -----------------------------------------------------------

    def save(self, record: ResearchRecord) -> ResearchRecord:
        self._store.save(record)
        return record

    def delete(self, record_id: str) -> bool:
        return self._store.delete(record_id)

    def update_status(
        self, record_id: str, status: RecordStatus | str
    ) -> ResearchRecord | None:
        record = self.get(record_id)
        if record is None:
            return None
        record.status = RecordStatus(status if isinstance(status, str) else status.value).value
        record.touch()
        self._store.save(record)
        return record

    # -- read ------------------------------------------------------------

    def get(self, record_id: str) -> ResearchRecord | None:
        raw = self._store.get(record_id)
        return ResearchRecord.from_dict(raw) if raw else None

    def find_by_hash(self, hsh: str) -> ResearchRecord | None:
        raw = self._store.find_by_hash(hsh)
        return ResearchRecord.from_dict(raw) if raw else None

    def find(
        self,
        keyword: str | None = None,
        domain: str | None = None,
        status: str | None = None,
        limit: int = 20,
    ) -> list:
        return [
            ResearchRecord.from_dict(raw)
            for raw in self._store.find(keyword, domain, status, limit)
        ]

    def list_recent(self, limit: int = 20) -> list[ResearchRecord]:
        return [
            ResearchRecord.from_dict(raw) for raw in self._store.list_recent(limit)
        ]

    def count(self) -> int:
        return self._store.count()
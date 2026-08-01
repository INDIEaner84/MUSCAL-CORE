import json
import os
import threading


class ReceiptStore:
    def __init__(self):
        self._store = {}
        self._lock = threading.RLock()

    def put(self, receipt_id, receipt):
        with self._lock:
            self._store[receipt_id] = receipt

    def get(self, receipt_id):
        with self._lock:
            return self._store.get(receipt_id)

    def all(self):
        with self._lock:
            return list(self._store.values())

    def all_ids(self):
        with self._lock:
            return list(self._store.keys())

    def remove(self, receipt_id):
        with self._lock:
            return self._store.pop(receipt_id, None)

    def count(self):
        with self._lock:
            return len(self._store)

    def clear(self):
        with self._lock:
            self._store.clear()


class FileReceiptStore(ReceiptStore):
    def __init__(self, directory="/tmp/muscal_receipts"):
        super().__init__()
        self._directory = directory

    def put(self, receipt_id, receipt):
        super().put(receipt_id, receipt)
        os.makedirs(self._directory, exist_ok=True)
        path = os.path.join(self._directory, f"{receipt_id}.json")
        try:
            data = receipt.to_dict() if hasattr(receipt, "to_dict") else {"receipt_id": receipt_id}
            with open(path, "w") as f:
                json.dump(data, f, indent=2, default=str)
        except Exception:
            pass

    def get(self, receipt_id):
        cached = super().get(receipt_id)
        if cached is not None:
            return cached
        path = os.path.join(self._directory, f"{receipt_id}.json")
        try:
            with open(path) as f:
                data = json.load(f)
            from features.tool_runtime.tool_runtime import ExecutionReceipt
            receipt = ExecutionReceipt.from_dict(data)
            super().put(receipt_id, receipt)
            return receipt
        except Exception:
            return None

    def persist_all(self):
        for rid in self.all_ids():
            _ = self.get(rid)

    def clear(self):
        super().clear()
        import glob
        for f in glob.glob(os.path.join(self._directory, "*.json")):
            try:
                os.remove(f)
            except Exception:
                pass

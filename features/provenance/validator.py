from datetime import datetime
from pathlib import Path
from typing import Optional

from features.provenance.classifier import EvidenceClassifier
from features.provenance.decision_writer import get_decision, get_decisions_by_trace
from features.provenance.models import EvidenceStatus


class ProvenanceValidator:

    def __init__(self, utr=None, db_path: Optional[Path] = None):
        self._utr = utr
        self._db_path = db_path

    def validate_execution_id(self, execution_id: str) -> dict:
        if self._utr is None:
            return {"status": EvidenceStatus.MISSING.value, "reason": "No UTR available"}
        store = getattr(self._utr, "_execution_store", {})
        if execution_id in store:
            return {"status": EvidenceStatus.VERIFIED.value, "reason": "execution_id found in store"}
        return {"status": EvidenceStatus.MISSING.value, "reason": "execution_id not found"}

    def validate_trace_id(self, trace_id: str) -> dict:
        if self._utr is None:
            return {"status": EvidenceStatus.MISSING.value, "reason": "No UTR available"}
        store = getattr(self._utr, "_execution_store", {})
        matching = [
            eid for eid, rec in store.items()
            if getattr(rec, "trace_id", "") == trace_id
        ]
        if matching:
            return {
                "status": EvidenceStatus.VERIFIED.value,
                "reason": f"trace_id found on {len(matching)} receipt(s)",
                "count": len(matching),
            }
        return {"status": EvidenceStatus.MISSING.value, "reason": "trace_id not on any receipt"}

    def validate_span_id(self, span_id: str) -> dict:
        if self._utr is None:
            return {"status": EvidenceStatus.MISSING.value, "reason": "No UTR available"}
        store = getattr(self._utr, "_execution_store", {})
        matching = [
            eid for eid, rec in store.items()
            if getattr(rec, "span_id", "") == span_id
        ]
        if matching:
            return {"status": EvidenceStatus.VERIFIED.value, "reason": f"span_id found on {len(matching)} receipt(s)"}
        return {"status": EvidenceStatus.MISSING.value, "reason": "span_id not found"}

    def validate_decision_id(self, decision_id: str) -> dict:
        if self._db_path is None:
            return {"status": EvidenceStatus.MISSING.value, "reason": "No DB path available"}
        dec = get_decision(self._db_path, decision_id)
        if dec is not None:
            return {"status": EvidenceStatus.VERIFIED.value, "reason": "decision_id found in DB"}
        return {"status": EvidenceStatus.MISSING.value, "reason": "decision_id not in DB"}

    def validate_receipt_provenance(self, receipt_id: str) -> dict:
        if self._utr is None:
            return {"status": EvidenceStatus.MISSING.value, "reason": "No UTR available"}
        store = getattr(self._utr, "_receipt_store", {})
        receipt = store.get(receipt_id)
        if receipt is None:
            return {"status": EvidenceStatus.MISSING.value, "reason": "receipt_id not found"}

        finalized = getattr(receipt, "finalized", False)
        if not finalized:
            return {"status": EvidenceStatus.INFERRED.value, "reason": "Receipt not finalized"}

        try:
            valid = receipt.verify_integrity()
            if valid:
                return {"status": EvidenceStatus.VERIFIED.value, "reason": "Integrity hash valid"}
            return {"status": EvidenceStatus.CONFLICT.value, "reason": "Integrity hash mismatch — tampered"}
        except Exception as e:
            return {"status": EvidenceStatus.INFERRED.value, "reason": f"Integrity check error: {e}"}

    def validate_verification_provenance(self, verification_id: str) -> dict:
        if self._utr is None:
            return {"status": EvidenceStatus.MISSING.value, "reason": "No UTR available"}
        store = getattr(self._utr, "_verification_store", {})
        vr = store.get(verification_id)
        if vr is None:
            return {"status": EvidenceStatus.MISSING.value, "reason": "verification_id not found"}

        if getattr(vr, "decision_id", ""):
            return {"status": EvidenceStatus.VERIFIED.value, "reason": "Verification has decision_id"}
        return {"status": EvidenceStatus.INFERRED.value, "reason": "Verification present, no decision_id"}

    def validate_decision_db(self, decision_id: str) -> dict:
        if self._db_path is None:
            return {"status": EvidenceStatus.MISSING.value, "reason": "No DB path available"}
        dec = get_decision(self._db_path, decision_id)
        if dec is None:
            return {"status": EvidenceStatus.MISSING.value, "reason": "decision_id not in DB"}
        receipt_trace = None
        if self._utr is not None:
            store = getattr(self._utr, "_execution_store", {})
            for rec in store.values():
                if getattr(rec, "decision_id", "") == decision_id:
                    receipt_trace = getattr(rec, "trace_id", "")
                    break
        db_trace = dec.get("trace_id", "")
        if receipt_trace and db_trace and receipt_trace != db_trace:
            return {
                "status": EvidenceStatus.CONFLICT.value,
                "reason": f"Receipt trace_id '{receipt_trace}' ≠ DB trace_id '{db_trace}'",
            }
        return {"status": EvidenceStatus.VERIFIED.value, "reason": "Decision DB record consistent"}

    def validate_cross_trace(self, execution_id: str) -> dict:
        if self._utr is None:
            return {"status": EvidenceStatus.MISSING.value, "reason": "No UTR available"}
        store = getattr(self._utr, "_execution_store", {})
        receipt = store.get(execution_id)
        if receipt is None:
            return {"status": EvidenceStatus.MISSING.value, "reason": "execution_id not found"}
        trace_id = getattr(receipt, "trace_id", "")
        if not trace_id:
            return {"status": EvidenceStatus.INFERRED.value, "reason": "No trace_id on receipt"}

        other_traces = set()
        for eid, rec in store.items():
            if eid == execution_id:
                continue
            t = getattr(rec, "trace_id", "")
            if t and t != trace_id:
                other_traces.add(t)
        if other_traces:
            return {
                "status": EvidenceStatus.VERIFIED.value,
                "reason": f"execution_id belongs to trace '{trace_id}', isolated from {len(other_traces)} other trace(s)",
            }
        return {
            "status": EvidenceStatus.INFERRED.value,
            "reason": f"execution_id belongs to trace '{trace_id}', no other traces for comparison",
        }

    def validate_all(self, execution_id: str) -> dict:
        return {
            "execution_id": self.validate_execution_id(execution_id),
            "trace_id": self.validate_trace_id(
                self._get_trace_id(execution_id)
            ) if execution_id else {"status": "MISSING"},
            "decision_id": self.validate_decision_id(
                self._get_decision_id(execution_id)
            ) if execution_id else {"status": "MISSING"},
        }

    def _get_trace_id(self, execution_id: str) -> str:
        if self._utr is None:
            return ""
        store = getattr(self._utr, "_execution_store", {})
        rec = store.get(execution_id)
        return getattr(rec, "trace_id", "") if rec else ""

    def _get_decision_id(self, execution_id: str) -> str:
        if self._utr is None:
            return ""
        store = getattr(self._utr, "_execution_store", {})
        rec = store.get(execution_id)
        return getattr(rec, "decision_id", "") if rec else ""

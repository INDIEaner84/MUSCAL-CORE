from features.provenance.models import EvidenceStatus, Relation


class EvidenceClassifier:

    PRECEDENCE = {
        EvidenceStatus.CONFLICT: 4,
        EvidenceStatus.VERIFIED: 3,
        EvidenceStatus.INFERRED: 2,
        EvidenceStatus.MISSING: 1,
    }

    @classmethod
    def resolve(cls, statuses: list[EvidenceStatus]) -> EvidenceStatus:
        if not statuses:
            return EvidenceStatus.MISSING
        return max(statuses, key=lambda s: cls.PRECEDENCE.get(s, 0))

    @classmethod
    def classify_relation(cls, source_id: str, target_id: str,
                          has_direct_evidence: bool = False,
                          has_integrity: bool = False,
                          has_db_record: bool = False,
                          temporal_proximity: bool = False,
                          has_conflict: bool = False) -> tuple[EvidenceStatus, str]:
        if has_conflict:
            return EvidenceStatus.CONFLICT, "Contradictory evidence from multiple sources"

        if has_direct_evidence and has_integrity and has_db_record:
            return EvidenceStatus.VERIFIED, "Direct authoritative evidence with integrity validation and DB record"

        if has_direct_evidence and has_integrity:
            return EvidenceStatus.VERIFIED, "Direct evidence with integrity validation"

        if has_direct_evidence:
            return EvidenceStatus.INFERRED, "Direct evidence present but not integrity-validated"

        if temporal_proximity:
            return EvidenceStatus.INFERRED, "Temporal/correlation evidence only"

        return EvidenceStatus.MISSING, "No evidence found in any source"

    @classmethod
    def classify_decision_link(cls, receipt_decision_id: str,
                               db_decision_id: str | None) -> tuple[EvidenceStatus, str]:
        if db_decision_id is None:
            if receipt_decision_id:
                return EvidenceStatus.MISSING, f"decision_id '{receipt_decision_id}' has no matching DB record"
            return EvidenceStatus.MISSING, "No decision_id on receipt"

        if receipt_decision_id and receipt_decision_id != db_decision_id:
            return EvidenceStatus.CONFLICT, (
                f"Receipt decision_id '{receipt_decision_id}' "
                f"≠ DB decision_id '{db_decision_id}'"
            )

        return EvidenceStatus.VERIFIED, "decision_id matches DB record"

    @classmethod
    def classify_trace_link(cls, receipt_trace_id: str,
                            db_trace_ids: list[str]) -> tuple[EvidenceStatus, str]:
        if not receipt_trace_id:
            return EvidenceStatus.MISSING, "No trace_id on receipt"

        if not db_trace_ids:
            return EvidenceStatus.INFERRED, f"trace_id '{receipt_trace_id}' from receipt, no DB decisions found"

        if receipt_trace_id in db_trace_ids:
            return EvidenceStatus.VERIFIED, f"trace_id '{receipt_trace_id}' matches decisions DB"

        return EvidenceStatus.INFERRED, f"trace_id '{receipt_trace_id}' on receipt, correlated with {len(db_trace_ids)} DB decisions via trace_id"

    @classmethod
    def classify_integrity(cls, receipt_finalized: bool,
                           hash_matches: bool) -> tuple[EvidenceStatus, str]:
        if not receipt_finalized:
            return EvidenceStatus.INFERRED, "Receipt not finalized, hash not computed"

        if hash_matches:
            return EvidenceStatus.VERIFIED, "SHA-256 integrity hash matches recomputed hash"

        return EvidenceStatus.CONFLICT, "SHA-256 integrity hash mismatch — receipt tampered"

    @classmethod
    def classify_orphan(cls, exists: bool, record_type: str) -> tuple[EvidenceStatus, str]:
        if exists:
            return EvidenceStatus.VERIFIED, f"{record_type} found in authoritative store"
        return EvidenceStatus.MISSING, f"{record_type} not found in any data source"

    @classmethod
    def classify_verification(cls, receipt_vs_db_match: bool,
                              decision_id_on_verification: bool) -> tuple[EvidenceStatus, str]:
        if not receipt_vs_db_match and decision_id_on_verification:
            return EvidenceStatus.CONFLICT, "Verification decision_id conflicts with receipt decision_id"

        if decision_id_on_verification:
            return EvidenceStatus.VERIFIED, "Verification has valid decision_id"

        return EvidenceStatus.INFERRED, "Verification result present, no decision_id linkage"

    @classmethod
    def reason(cls, status: EvidenceStatus, relation: str) -> str:
        reasons = {
            EvidenceStatus.VERIFIED: f"'{relation}' is directly supported by authoritative persisted data",
            EvidenceStatus.INFERRED: f"'{relation}' is derived from evidence but not explicitly persisted as causal",
            EvidenceStatus.MISSING: f"'{relation}' cannot be established from available data",
            EvidenceStatus.CONFLICT: f"Multiple authoritative or high-confidence sources disagree on '{relation}'",
        }
        return reasons.get(status, "Unknown classification")

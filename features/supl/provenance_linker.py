from __future__ import annotations
import time
from typing import Any, Dict, List, Optional

from features.supl.provenance import UIInteraction, InvalidInteractionTransition
from features.supl.semantic_model import InteractionStatus
from features.supl.event_integration import EventBusBridge


class ProvenanceLinker:
    def __init__(self, bridge: Optional[EventBusBridge] = None):
        self._bridge = bridge
        self._links: Dict[str, Dict[str, Optional[str]]] = {}

    def link(
        self,
        interaction: UIInteraction,
        receipt: Any = None,
        verification: Any = None,
    ) -> None:
        interaction_id = interaction.interaction_id
        if not interaction_id:
            raise ValueError("interaction_id is required")

        chain: Dict[str, Optional[str]] = {
            "interaction_id": interaction_id,
            "execution_id": interaction.execution_id,
            "receipt_id": interaction.receipt_id,
            "verification_id": interaction.verification_id,
        }

        if receipt is not None:
            rid = receipt.receipt_id if hasattr(receipt, "receipt_id") else None
            eid = receipt.execution_id if hasattr(receipt, "execution_id") else None
            if rid:
                chain["receipt_id"] = rid
            if eid:
                chain["execution_id"] = eid

        if verification is not None:
            vid = verification.verification_id if hasattr(verification, "verification_id") else None
            if vid:
                chain["verification_id"] = vid

        if chain["execution_id"] and not interaction.execution_id:
            interaction.execution_id = chain["execution_id"]
        if chain["receipt_id"] and not interaction.receipt_id:
            interaction.receipt_id = chain["receipt_id"]
        if chain["verification_id"] and not interaction.verification_id:
            interaction.verification_id = chain["verification_id"]

        self._links[interaction_id] = chain

        if self._bridge:
            self._bridge.publish_provenance_linked(
                interaction_id,
                chain.get("execution_id") or "",
                chain.get("receipt_id") or "",
            )

    def get_chain(self, interaction_id: str) -> Optional[Dict[str, Optional[str]]]:
        return self._links.get(interaction_id)

    def validate_consistency(self, interaction_id: str, execution_id: str, receipt_id: str) -> bool:
        chain = self._links.get(interaction_id)
        if chain is None:
            return False
        if chain.get("execution_id") and chain["execution_id"] != execution_id:
            return False
        if chain.get("receipt_id") and chain["receipt_id"] != receipt_id:
            return False
        return True

    def has_inconsistent_chain(self, interaction_id: str) -> bool:
        chain = self._links.get(interaction_id)
        if chain is None:
            return False
        eid = chain.get("execution_id")
        rid = chain.get("receipt_id")
        if eid and rid:
            return False
        return False

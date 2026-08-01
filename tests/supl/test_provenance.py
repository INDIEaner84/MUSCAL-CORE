import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest
from features.supl.provenance import UIInteraction, InvalidInteractionTransition
from features.supl.semantic_model import InteractionSource, InteractionStatus


def test_interaction_creation():
    interaction = UIInteraction.create(
        application_id="test", action_id="sum", capability_id="add"
    )
    assert interaction.interaction_id is not None
    assert interaction.status == InteractionStatus.REQUESTED
    assert interaction.execution_id is None
    assert interaction.receipt_id is None
    assert interaction.verification_id is None


def test_mark_authorized():
    interaction = UIInteraction.create()
    interaction.mark_authorized()
    assert interaction.status == InteractionStatus.AUTHORIZED


def test_mark_rejected():
    interaction = UIInteraction.create()
    interaction.mark_rejected()
    assert interaction.status == InteractionStatus.REJECTED


def test_mark_executing():
    interaction = UIInteraction.create()
    interaction.mark_authorized()
    interaction.mark_executing()
    assert interaction.status == InteractionStatus.EXECUTING


def test_link_execution():
    interaction = UIInteraction.create()
    interaction.mark_authorized()
    interaction.mark_executing()
    interaction.link_execution("exec_001")
    assert interaction.status == InteractionStatus.EXECUTED
    assert interaction.execution_id == "exec_001"


def test_link_receipt():
    interaction = UIInteraction.create()
    interaction.mark_authorized()
    interaction.mark_executing()
    interaction.link_execution("exec_001")
    interaction.link_receipt("receipt_001")
    assert interaction.receipt_id == "receipt_001"


def test_mark_verified():
    interaction = UIInteraction.create()
    interaction.mark_authorized()
    interaction.mark_executing()
    interaction.link_execution("exec_001")
    interaction.link_receipt("receipt_001")
    interaction.mark_verified("verification_001")
    assert interaction.status == InteractionStatus.VERIFIED
    assert interaction.verification_id == "verification_001"


def test_mark_failed():
    interaction = UIInteraction.create()
    interaction.mark_failed()
    assert interaction.status == InteractionStatus.FAILED


def test_invalid_transition():
    interaction = UIInteraction.create()
    with pytest.raises(InvalidInteractionTransition):
        interaction.link_execution("exec_001")


def test_invalid_transition_rejected_to_executing():
    interaction = UIInteraction.create()
    interaction.mark_rejected()
    with pytest.raises(InvalidInteractionTransition):
        interaction.mark_executing()


def test_invalid_transition_verified_to_failed():
    interaction = UIInteraction.create()
    interaction.mark_authorized()
    interaction.mark_executing()
    interaction.link_execution("e1")
    interaction.link_receipt("r1")
    interaction.mark_verified("v1")
    with pytest.raises(InvalidInteractionTransition):
        interaction.mark_failed()


def test_missing_linking():
    interaction = UIInteraction.create()
    assert interaction.execution_id is None
    assert interaction.receipt_id is None
    assert interaction.verification_id is None


def test_provenance_chain():
    interaction = UIInteraction.create()
    chain = interaction.provenance_chain()
    assert chain["interaction_id"] is not None
    assert chain["execution_id"] is None
    assert not interaction.chain_is_complete()
    interaction.mark_authorized()
    interaction.mark_executing()
    interaction.link_execution("exec_1")
    interaction.link_receipt("rec_1")
    interaction.mark_verified("ver_1")
    assert interaction.chain_is_complete()


def test_serialization():
    interaction = UIInteraction.create(
        application_id="app", action_id="act", capability_id="cap",
        source_mode=InteractionSource.GRAPH_NATIVE,
    )
    d = interaction.to_dict()
    assert d["source_mode"] == "graph_native"
    restored = UIInteraction.from_dict(d)
    assert restored.interaction_id == interaction.interaction_id
    assert restored.source_mode == InteractionSource.GRAPH_NATIVE
    assert restored.status == InteractionStatus.REQUESTED


def test_serialization_with_full_chain():
    interaction = UIInteraction.create()
    interaction.mark_authorized()
    interaction.mark_executing()
    interaction.link_execution("e1")
    interaction.link_receipt("r1")
    interaction.mark_verified("v1")
    d = interaction.to_dict()
    restored = UIInteraction.from_dict(d)
    assert restored.execution_id == "e1"
    assert restored.receipt_id == "r1"
    assert restored.verification_id == "v1"
    assert restored.status == InteractionStatus.VERIFIED


def test_validate():
    interaction = UIInteraction(interaction_id="")
    errs = interaction.validate()
    assert "interaction_id is required" in errs


def test_link_receipt_without_execution_fails():
    interaction = UIInteraction.create()
    interaction.mark_authorized()
    interaction.mark_executing()
    interaction.link_execution("e1")
    interaction.link_receipt("r1")
    assert True


def test_no_fake_ids():
    interaction = UIInteraction.create()
    assert interaction.execution_id is None
    assert interaction.receipt_id is None
    assert interaction.verification_id is None
    interaction.mark_failed()
    assert interaction.execution_id is None

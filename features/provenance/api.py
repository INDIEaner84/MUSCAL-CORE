from pathlib import Path
from typing import Optional

from features.provenance.resolver import ProvenanceResolver


def get_resolver(utr=None, db_path: Optional[Path] = None,
                 graph_state=None, event_bus=None) -> ProvenanceResolver:
    return ProvenanceResolver(utr=utr, db_path=db_path,
                              graph_state=graph_state, event_bus=event_bus)


def reconstruct_execution(execution_id: str, utr=None,
                          db_path: Optional[Path] = None) -> dict:
    resolver = get_resolver(utr=utr, db_path=db_path)
    report = resolver.resolve_execution(execution_id)
    return report.to_dict()


def inspect_provenance(execution_id: str, utr=None,
                       db_path: Optional[Path] = None) -> dict:
    resolver = get_resolver(utr=utr, db_path=db_path)
    return resolver.inspect_provenance(execution_id)


def validate_provenance(execution_id: str, utr=None,
                        db_path: Optional[Path] = None) -> dict:
    resolver = get_resolver(utr=utr, db_path=db_path)
    return resolver.validate_provenance(execution_id)


def get_evaluator(utr=None, db_path: Optional[Path] = None,
                  graph_state=None, event_bus=None):
    from features.provenance.evaluation import MetaEvaluator
    return MetaEvaluator(utr=utr, db_path=db_path,
                         graph_state=graph_state, event_bus=event_bus)


def evaluate_execution(execution_id: str, utr=None,
                       db_path: Optional[Path] = None) -> dict:
    evaluator = get_evaluator(utr=utr, db_path=db_path)
    report = evaluator.evaluate(execution_id)
    return report.to_dict()

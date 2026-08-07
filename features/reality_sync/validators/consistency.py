"""Konsistenz-Prüfung für den Runtime- und Canonical-State.

Der Drift-Vergleich und der Proposal-Prozess müssen gegen einen gültigen
State laufen. Ungültige Eingaben werden abgelehnt (kein Drift-Report).
"""

from __future__ import annotations

from typing import Any


class InvalidStateError(ValueError):
    """Raised wenn der übergebene State nicht konsistent ist."""


REQUIRED_SECTIONS = ("entities", "graph_nodes", "active_tasks", "agents")


class ConsistencyValidator:
    """Validierung, dass beide Seiten des Vergleichs wohlgeformt sind.

    Akzeptiert Dictionaries oder Objekte mit ``to_dict()`` (z. B.
    den ``ReconstructedState`` aus ``features/events/state_model``).
    Grundbedingung: mindestens eine Anforderungssektion vorhanden.
    """

    def validate(self, state: Any) -> dict:
        data = self._coerce(state)
        if not isinstance(data, dict):
            raise InvalidStateError(
                f"State muss ein dict sein, got {type(state).__name__}"
            )

        missing = [s for s in REQUIRED_SECTIONS if s not in data]
        if missing:
            raise InvalidStateError(
                f"State fehlt Pflichtsektion(en): {', '.join(missing)}"
            )

        for section in REQUIRED_SECTIONS:
            value = data[section]
            if not isinstance(value, dict):
                raise InvalidStateError(f"Sektion '{section}' muss ein dict sein")

        if data.get("timestamp") is None:
            raise InvalidStateError("State hat keinen gueltigen timestamp")

        return data

    def compare_valid(self, runtime_state: Any, canonical_state: Any) -> bool:
        try:
            self.validate(runtime_state)
            self.validate(canonical_state)
            return True
        except (InvalidStateError, ValueError, TypeError):
            return False

    def _coerce(self, state: Any) -> Any:
        if hasattr(state, "to_dict") and callable(getattr(state, "to_dict")):
            return state.to_dict()
        return state


__all__ = ["ConsistencyValidator", "InvalidStateError"]
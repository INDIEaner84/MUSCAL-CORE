# MUSCAL CORE — Known Failures & Issues (Baseline)

**Erstellt:** 2026-07-08
**Zweck:** Alle bekannten Probleme vor Phase 1 dokumentieren.

---

## C1 — Graph Growth Drift

| Aspekt | Wert |
|--------|------|
| **Beschreibung** | Jeder `kernel.run()` erzeugt ~9 neue Graph-Nodes, auch bei identischem Input |
| **Ort** | `kernel.py` pipeline: RAG → MKC → Bridge → MEL → Feedback → Memory → Graph |
| **Nachweis** | Stress-Test Drift Check: 900→918 Nodes bei 2x "drift check input" |
| **Ursache** | RAG akkumuliert History in `get_recent()`, MKC erzeugt neue Nodes pro Aufruf |
| **Status** | ✅ **GEMITIGATED** — `features/runtime/graph_manager.py` pruned nach jedem Run (SOFT_LIMIT=500, HARD_LIMIT=3000) mit semantischem Scoring |
| **Risiko** | 🟢 Niedrig — Graph wächst maximal bis HARD_LIMIT, dann smarter Prune |

## C2 — Lambda Closure im EventBus

| Aspekt | Wert |
|--------|------|
| **Beschreibung** | Lambda-Closure-Bug im EventBus: `lambda: handle(evt)` behält letzte Referenz |
| **Ort** | `kernel.py` Zeile 160 + 165 (Listener-Registrierung) |
| **Nachweis** | `tests/test_lambda_closure.py` — **beide Tests PASSEN** |
| **Status** | ✅ Bereits gefixt (Tests bestätigen korrektes Verhalten) |
| **Schwere** | 🟢 Gelöst |

## C3 — Stub-Dateien <20 Zeilen

| Aspekt | Wert |
|--------|------|
| **Beschreibung** | Python-Dateien <20 Zeilen |
| **Kategorien** | 25 Package `__init__.py` (behalten), 9 Active Minimal (behalten), 41 Placeholder (Roadmap), 6 Unklar (geprüft), restliche DEAD/DUPLIKAT archiviert |
| **Status** | ✅ **TEILWEISE GELÖST** — `event_node.py`, `vector_memory.py` archiviert (keine aktiven Imports). `memory_system.py`, `meta_compiler.py`, `compiler_updater.py`, `compiler_validator.py`, `compiler_state.py` bereits gelöscht. 41 Placeholder-Stubs auf Roadmap belassen. |
| **Risiko** | 🟢 Niedrig — keine dead imports mehr, keine broken imports |

## C4 — Keine reproduzierbare Installation

| Aspekt | Wert |
|--------|------|
| **Beschreibung** | `requirements.txt` vorhanden, aber kein `requirements.lock` oder `pyproject.toml` mit pins |
| **Risiko** | 🟡 Mittel — unterschiedliche Umgebungen → unterschiedliches Verhalten |

## C5 — Kein .gitignore / kein Git-Repository

| Aspekt | Wert |
|--------|------|
| **Beschreibung** | `__pycache__/`, `*.db`, `logs/` nicht versioniert aber ungeschützt |
| **Risiko** | 🟢 Niedrig — lokales Entwicklungshindernis |

## C6 — Memory-Drift ohne Auto-Reset

| Aspekt | Wert |
|--------|------|
| **Beschreibung** | `mkc_rules.py` SIGNAL_RULES.confidence mutiert durch Feedback ohne Auto-Reset |
| **Status** | ✅ **GEMITIGATED** — `features/runtime/confidence_reset.py` ruft alle 10 Runs `reset_state()` auf, wenn Gesamtdrift > 0.5 |
| **Risiko** | 🟢 Niedrig — automatischer Reset bei Über-Drift |

## C7 — Keine DB-Migrationen

| Aspekt | Wert |
|--------|------|
| **Beschreibung** | SQLite Schema wird via `CREATE TABLE IF NOT EXISTS` erstellt, keine ALTER / Migration |
| **Status** | ✅ **GELÖST** — `scripts/migrate_sqlite.py` unterstützt versionierte Migrations (`@_migration`-Decorator) mit `schema_version`-Tracking |
| **Risiko** | 🟢 Gelöst |

## C8 — FIFO-Prune ohne Semantik

| Aspekt | Wert |
|--------|------|
| **Beschreibung** | Graph-Prune entfernt älteste Nodes, nicht unwichtigste |
| **Status** | ✅ **GEMITIGATED** — `features/runtime/graph_manager.py` implementiert semantischen Prune (Connectivity + Recency) vor FIFO-Härtelimite |
| **Risiko** | 🟢 Niedrig — smarter Prune erhält wichtige Nodes |

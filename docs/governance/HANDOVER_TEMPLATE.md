# MUSCAL CORE — SESSION HANDOVER (MSCE)

**Zweck:** Standardisierte Vorlage für Session-Handover-Dokumente.
**Regel:** Pflicht bei Dateiänderungen. Wird in `docs/session_handovers/` gespeichert.

---

## Verwendung

1. Kopiere diese Vorlage nach `docs/session_handovers/HANDOVER_[SESSION_ID].md`
2. Ersetze alle `[PLACEHOLDER]` durch tatsächliche Werte
3. Lösche unbenutzte Sektionen
4. Füge der SESSION_REGISTRY.md den Session-Eintrag hinzu

---

## Vorlage

```
# SESSION HANDOVER — [SESSION_ID]

**Date:** [DATE]
**Duration:** [DURATION]
**Category:** [CATEGORY]

## Session Summary

[1-3 Sätze über das Erreichte]

## Files Changed

| File | Change Type | Reason |
|------|-------------|--------|
| [path] | [NEW/MODIFIED/DELETED] | [warum] |

## State Changes

- [Welcher Zustand wurde verändert]
- [Welcher Zustand wurde erstellt]
- [Welcher Zustand wurde zerstört]

## Open Items

| Item | Status | Next Action |
|------|--------|-------------|
| [item] | [BLOCKED/DONE/DEFERRED] | [was als Nächstes zu tun ist] |

## Blockers

- [Aufgetretene Blocker]

## Verification

- [ ] Tests bestanden: [command]
- [ ] Git diff überprüft
- [ ] Keine Core-Dateien modifiziert (oder Override dokumentiert)

## Next Session Should

1. [Erste Priorität]
2. [Zweite Priorität]
3. [Dritte Priorität]
```

---

## Ablage

Handover-Dateien werden gespeichert als:
```
docs/session_handovers/HANDOVER_S-YYYY-MM-DD-NNN.md
```

---

## Checklist (vor Session-Ende)

- [ ] Incomplete Tasks → WORK_QUEUE.md verschoben
- [ ] SESSION_HANDOVER erstellt (wenn Dateien geändert)
- [ ] SESSION_REGISTRY.md aktualisiert
- [ ] CHECKPOINT_INDEX.md aktualisiert (wenn Meilenstein)
- [ ] ACTIVE_TASKS.md geleert
- [ ] Git Commit durchgeführt

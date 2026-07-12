# MUSCAL CORE — SESSION_OWNERSHIP

**Zweck:** Ownership-Modell für Sessions — wer darf was.

---

## Ownership Model

| Rolle | Verantwortung | Genehmigungsbefugnis |
|-------|---------------|----------------------|
| Hermes Agent (AI) | Ausführung, Dokumentation, SESSION_HANDOVER | Level 0–1 |
| Human Operator | Freigabe, Architecture Review, Core Approval | Level 2–3 |

---

## Agent Ownership

- Hermes Agent führt Session durch, erstellt HANDOVER, aktualisiert REGISTRY
- Agent darf Level 0–1 Änderungen selbstständig durchführen
- Agent MUSS bei Level 2–3 vorher Approval einholen

---

## Human Approval Grenzen

| Level | Genehmigung |
|-------|-------------|
| 0 | Keine menschliche Approval nötig |
| 1 | Review durch Human |
| 2 | Architecture Review durch Human |
| 3 | ADR + Architecture Review + explizite Freigabe durch Human |

---

## Lock-Level Bezug

→ Siehe `docs/LOCK_PROTOCOL.md`

---

## Ownership Transfer

Eine Session kann Ownership an eine Folgesession übergeben.

**Voraussetzungen:**
- SESSION_HANDOVER vorhanden
- offene Tasks dokumentiert
- Lock-Level bekannt
- Approval Status dokumentiert

# TECHNICAL_MANUAL_CONFLICT_REPORT — 3-Way Reconciliation

**Audit:** MUSCAL-KRA-2026-08-01 · **Layer:** RAW FACT / EXTRACTED METADATA / INFERRED
**Source:** S3 + S7 · **Date:** 2026-08-01 · **Method:** structural diff + claim verification against current repo state

---

## 1. The Three Manuals

| ID | File | Version | Lines | Last Modified | Claims |
|----|------|---------|-------:|---------------|--------|
| M-ROOT | `Codebase/TECHNICAL_MANUAL.md` | **v0.5** (July 2026), English | 932 | 2026-07-02 | "~237 files across two coexisting codebases" |
| M-0.6 | `MUSCAL CORE/docs/history/technical_manual_v0.6.md` | **v0.6** (Juli 2026), German | 1,935 | 2026-07-12 | "~184 Python-Dateien, ~10.744 LOC, ~225 Dateien gesamt" · "Late Alpha / Early Beta, ~45% Stubs" |
| M-0.7 | `MUSCAL CORE/TECHNICAL_MANUAL_v0.7.md` | **v0.7** (Juli 2026), German | 371 | 2026-07-15 | same counts as v0.6 · "Stable Prototype" |

**Key structural fact [C0]:** M-0.7 (371 lines) is an **abridged stabilization manual** (28 sections vs M-0.6's 137). M-0.6 is the full manual. M-ROOT describes *two codebases* (`muscal/` + `MUSCAL CORE/`) and is the only manual covering the `muscal/` package.

## 2. Claim Comparison Table

| Claim | M-ROOT | M-0.6 | M-0.7 | Verified reality (2026-08-01) | Verdict |
|-------|--------|-------|-------|-------------------------------|---------|
| Version | 0.5 | 0.6 | 0.7 | CHANGELOG_v0.8.md exists; no v0.8 manual | ⚠️ Version drift |
| Python files | ~57 (muscal) + ~157 (CORE) | ~184 | ~184 (copied) | **611** (CORE) | ❌ All undercount |
| LOC | — | ~10,744 | ~10,744 (copied) | **77,376** (CORE) | ❌ 7.2× undercount |
| Total files | ~237 | ~225 | ~225 (copied) | **1,209** (CORE) | ❌ 5.4× undercount |
| Status | — | Late Alpha / ~45% Stubs | Stable Prototype | PROJECT_STATE: "READY WITH RISKS"; audits: Conditional GO | ⚠️ divergent |
| Tests | — | (not stated) | §8: **"Keine Tests (0 Test-Dateien)"** | **2,869 test functions / 204 files**; PROJECT_STATE: 547/547 | ❌ Internal + external contradiction |
| Stubs | — | ~45% | §8: "~45% Stubs (~80 Dateien <20 Zeilen)" UNRESOLVED | `archive/stubs/` contains 1 file; PROJECT_STATE: "alle 28 Stubs gelöscht" | ❌ Contradictory |
| `kernel.py` size | — | — | 417 lines | **708** | ❌ +291 |
| `memory.py` size | — | — | 139 lines | **162** | ❌ +23 |
| `graph.py` size | — | — | 219 lines | **279** | ❌ +60 |
| `event_bus.py` size | — | — | 74 lines | **111** | ❌ +37 |
| Language | English | German | German | (code comments mixed) | ℹ️ |
| Scope | two codebases | CORE only | CORE only | — | ℹ️ |

## 3. Conflict Classification

### CRITICAL
- **TC-C1 [C0] — M-0.7 internal contradiction:** claims "Stable Prototype" (header) while §8 "Bekannte Probleme" lists *"Keine Tests (0 Test-Dateien)"* and *"~45% Stubs"* as **❌ Ungelöst** — in the very same document. Either the status or the problem table is wrong.
- **TC-C2 [C0] — test-count contradiction:** M-0.7 §8 "0 Test-Dateien" vs PROJECT_STATE (20.07) "547/547 passed" vs actual 2,869 test functions vs audit-subset counts (431 Trust Core / 384 / 812 E3.2). There is **no consistent test-count story anywhere**; each document counts a different subset without stating the subset.

### HIGH
- **TC-H1 [C0] — copied LOC claims:** M-0.7 reproduces M-0.6's exact numbers ("~184 / ~10.744 / ~225") without verification; both are far below reality (611 / 77,376 / 1,209). The numbers describe **no identifiable scope** (root-only = 99/7,803; full = 611/77,376) [C0].
- **TC-H2 [C0] — per-file line counts outdated:** all four module sizes in M-0.7 §4 are below current file sizes; manual reflects ≈12.07 snapshot.
- **TC-H3 [C1] — version hierarchy undefined:** M-ROOT (v0.5) is the *newest-modified* manual in `Codebase/` root but oldest version; M-0.7 is newest version but an excerpt. No document states "this supersedes X".

### MEDIUM
- **TC-M1 [C0] — dual-codebase scope:** M-ROOT is the only source describing `muscal/`; the other two ignore it. Knowledge consumers reading only M-0.7 would miss an entire codebase.
- **TC-M2 [C1] — status vocabulary drift:** "Late Alpha / Early Beta" → "Stable Prototype" → PROJECT_STATE "READY WITH RISKS" → chat-based "CONDITIONAL GO" — the same project has 4 different status words with no mapping between them.

### LOW
- **TC-L1 [C1] — dependency lists duplicated:** M-0.7 §7 lists `requirements.txt` "vollständig" while `requirements.lock` and `spec.yaml` also exist — which is authoritative is unstated.
- **TC-L2 [C2] — E3.1-PHASE2-REPORT.md and E3.3_EXECUTION_LEDGER.md are untracked** (see REPOSITORY_CENSUS §7) — they exist on disk but not in git.

## 4. Which Manual Should Win?

| Criterion | M-ROOT | M-0.6 | M-0.7 |
|-----------|--------|-------|-------|
| Latest version number | ❌ 0.5 | 0.6 | ✅ 0.7 |
| Full coverage | ✅ both codebases | CORE | excerpt only |
| Factual accuracy (LOC/modules) | ~ | ❌ | ❌ |
| Internal consistency | ~ | ✅ | ❌ |
| Match to PROJECT_STATE | ~ | ❌ (alpha) | ~ (stable) |

**Recommendation [HYP, requires human decision]:** No manual is currently trustworthy as a whole. The recommended fix is to **generate one canonical `TECHNICAL_MANUAL_v0.8.md`** from verified repo data (census numbers, current module sizes, actual test counts per scope) and mark M-ROOT/M-0.6/M-0.7 as `docs/history/` legacy. Until then, **no manual claim should be cited as authoritative** — code + PROJECT_STATE + audits take precedence.

## 5. Evidence Index

- M-ROOT header & §1.1: `Codebase/TECHNICAL_MANUAL.md` lines 1–30
- M-0.6 header: `MUSCAL CORE/docs/history/technical_manual_v0.6.md` lines 1–12
- M-0.7 header + §4 + §8 + §9: `MUSCAL CORE/TECHNICAL_MANUAL_v0.7.md`
- Actual line counts: `wc -l` on core modules (REPOSITORY_CENSUS §4)
- Test functions: `grep -r "def test_" tests/` → 2,869
- PROJECT_STATE.md (20.07): 547/547, stubs deleted
- MC-TC-007_STATUS_ZUSAMMENFASSUNG.md (31.07 chat input): 384/384, Conditional GO

*All claims verified by direct file inspection on 2026-08-01; confidence tags per AUDIT_SCOPE.md §5.*

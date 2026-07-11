# MUSCAL Test Coverage Policy

## Zweck

Richtlinien und Ziele für die Testabdeckung.

---

## Abdeckungsziele

```yaml
Coverage Targets:
  Overall: >80%
  
  By Component:
    Core Agents: >90%
    Governance Agents: >85%
    Business Agents: >80%
    Ops Agents: >85%
  
  By Type:
    Unit Tests: >80%
    Integration Tests: >70%
    E2E Tests: >60%
```

---

## Abdeckungstypen

### Code Coverage

```yaml
Code Coverage:
  Line Coverage: >80%
  Branch Coverage: >75%
  Function Coverage: >90%
  
  Tools:
    - coverage.py
    - pytest-cov
    - coveralls
```

### Requirement Coverage

```yaml
Requirement Coverage:
  Functional Requirements: 100%
  Non-Functional Requirements: >80%
  
  Mapping:
    - Each requirement -> test cases
    - Traceability matrix
```

### API Coverage

```yaml
API Coverage:
  Endpoints: 100%
  Methods: 100%
  Status Codes: >90%
  
  Testing:
    - Happy path
    - Error cases
    - Edge cases
```

---

## Messung

### Tools

```yaml
Coverage Tools:
  Python:
    - coverage.py
    - pytest-cov
  
  JavaScript:
    - Istanbul/nyc
    - Jest
  
  Reports:
    - HTML
    - XML (Cobertura)
    - JSON
```

### Konfiguration

```ini
# .coveragerc
[run]
source = muscal
omit = 
    tests/*
    */migrations/*
    */__pycache__/*

[report]
fail_under = 80
show_missing = True
precision = 2

[html]
directory = htmlcov
```

---

## Berichte

### Weekly Coverage Report

```yaml
Weekly Report:
  Sections:
    - Overall Coverage
    - Coverage by Component
    - Coverage by Type
    - Uncovered Code
    - Recommendations
  
  Format: Markdown + HTML
  Recipients: Development Team
```

### Coverage Trends

```yaml
Trend Analysis:
  Metrics:
    - Coverage over time
    - New code coverage
    - Changed code coverage
  
  Alerts:
    - Coverage drops below threshold
    - New code below coverage target
```

---

## Regeln

```yaml
Coverage Rules:
  Pre-Commit:
    - No coverage decrease allowed
  
  Pre-Merge:
    - Coverage must meet threshold
    - All tests must pass
  
  Pre-Release:
    - Full coverage report required
    - No critical uncovered code
```

---

## Uncovered Code Management

```yaml
Uncovered Code:
  Process:
    1. Identify uncovered code
    2. Classify risk level
    3. Create test plan
    4. Add tests
    5. Verify coverage
  
  Low Risk:
    - Accept temporarily
    - Add to backlog
  
  Medium Risk:
    - Add tests within 1 sprint
  
  High Risk:
    - Add tests before release
```

---

## Dokumente

```
testing/
├── COVERAGE.md
├── .coveragerc
├── coverage_reports/
└── coverage_history/
```

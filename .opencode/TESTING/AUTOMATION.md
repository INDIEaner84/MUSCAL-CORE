# MUSCAL Test Automation

## Zweck

Automatisierung des Testprozesses für CI/CD.

---

## CI/CD Pipeline

```
Code Commit
    ↓
Linting
    ↓
Unit Tests
    ↓
Integration Tests
    ↓
Coverage Report
    ↓
E2E Tests (optional)
    ↓
Deployment
```

---

## Pipeline Stufen

### Stage 1: Linting

```yaml
Linting:
  Tools:
    - flake8
    - black
    - isort
    - mypy
  
  Rules:
    - Code style compliance
    - Type checking
    - Import sorting
  
  Fail: On error
```

### Stage 2: Unit Tests

```yaml
Unit Tests:
  Framework: pytest
  
  Commands:
    - pytest tests/unit/ -v --cov=muscal
  
  Parallel: Yes
  
  Timeout: 5 minutes
  
  Fail: On failure
```

### Stage 3: Integration Tests

```yaml
Integration Tests:
  Framework: pytest
  
  Commands:
    - pytest tests/integration/ -v
  
  Services:
    - Database (PostgreSQL)
    - Redis
  
  Timeout: 15 minutes
  
  Fail: On failure
```

### Stage 4: Coverage

```yaml
Coverage:
  Tools:
    - pytest-cov
    - coveralls
  
  Threshold: 80%
  
  Reports:
    - HTML (local)
    - XML (CI)
    - Coveralls (cloud)
  
  Fail: Below threshold
```

### Stage 5: E2E Tests

```yaml
E2E Tests:
  Framework: Playwright
  
  Commands:
    - playwright test tests/e2e/
  
  Browsers:
    - Chromium
  
  Timeout: 30 minutes
  
  Fail: On critical failure
```

---

## GitHub Actions

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-test.txt
      
      - name: Lint
        run: |
          flake8 muscal/
          black --check muscal/
      
      - name: Unit Tests
        run: pytest tests/unit/ -v --cov=muscal
      
      - name: Integration Tests
        run: pytest tests/integration/ -v
      
      - name: Coverage Report
        uses: codecov/codecov-action@v3
```

---

## Test Reporting

```yaml
Reporting:
  Format:
    - JUnit XML (CI)
    - HTML (local)
    - Allure (detailed)
  
  Metrics:
    - Tests passed/failed
    - Duration
    - Coverage
    - Flaky tests
  
  Notifications:
    - Slack (on failure)
    - Email (on failure)
```

---

## Test Data Management

```yaml
Test Data:
  Strategy:
    - Fixtures (static)
    - Factories (dynamic)
    - Seed data (database)
  
  Isolation:
    - Each test creates own data
    - Cleanup after each test
    - No shared state
  
  Environment:
    - Test database
    - Mock external services
    - Controlled time
```

---

## Dokumente

```
testing/
├── AUTOMATION.md
├── .github/workflows/test.yml
├── pytest.ini
└── conftest.py
```

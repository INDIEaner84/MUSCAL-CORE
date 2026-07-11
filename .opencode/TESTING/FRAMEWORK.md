# MUSCAL Testing Framework

## Zweck

Test-Framework-Design für das gesamte MUSCAL System.

---

## Test Pyramide

```
         /\
        /  \      E2E Tests (10%)
       /----\
      /      \    Integration Tests (20%)
     /--------\
    /          \  Unit Tests (70%)
   /------------\
```

---

## Test Typen

### Unit Tests

```yaml
Unit Tests:
  Ziel: Einzelne Funktionen/Klassen testen
  
  Abdeckung: >80%
  Geschwindigkeit: <100ms pro Test
  Isolation: Keine externen Abhängigkeiten
  
  Framework: pytest
  Mocking: unittest.mock
  Fixtures: pytest fixtures
```

### Integration Tests

```yaml
Integration Tests:
  Ziel: Interaktion zwischen Komponenten testen
  
  Abdeckung: Alle APIs und Interfaces
  Geschwindigkeit: <5s pro Test
  Isolation: Test-Database/Mocks
  
  Framework: pytest + requests
  Database: Test-DB (SQLite/PostgreSQL)
  API: Test-Server
```

### E2E Tests

```yaml
E2E Tests:
  Ziel: Komplette Workflows testen
  
  Abdeckung: Kritische Pfade
  Geschwindigkeit: <30s pro Test
  Isolation: Vollständige Testumgebung
  
  Framework: Playwright / Selenium
  Browser: Chromium
  Reporting: Allure
```

---

## Test Struktur

```
tests/
├── unit/
│   ├── agents/
│   ├── core/
│   └── services/
├── integration/
│   ├── api/
│   ├── database/
│   └── agents/
├── e2e/
│   ├── workflows/
│   └── scenarios/
├── fixtures/
├── helpers/
└── conftest.py
```

---

## Test Naming

```python
# Function: test_[function_name]_[scenario]_[expected]
def test_process_task_valid_input_returns_success():
    pass

def test_process_task_invalid_input_raises_error():
    pass

# Class: Test[ClassName]
class TestMetaOrchestrator:
    def test_select_agent_valid_task_returns_agent():
        pass
    
    def test_select_agent_no_suitable_agent_returns_none():
        pass
```

---

## Fixtures

```python
# conftest.py
@pytest.fixture
def agent():
    return MockAgent(id="AGT-001", name="TestAgent")

@pytest.fixture
def task():
    return Task(id="task-001", type="testing", priority="high")

@pytest.fixture
def event_bus():
    return MockEventBus()

@pytest.fixture
def shared_memory():
    return MockSharedMemory()
```

---

## Mocking

```python
# Mock Agent
class MockAgent:
    def __init__(self, id, name):
        self.id = id
        self.name = name
        self.status = "active"
    
    async def process_task(self, task):
        return {"status": "success", "result": "mocked"}

# Mock Event Bus
class MockEventBus:
    def __init__(self):
        self.events = []
    
    async def publish(self, event):
        self.events.append(event)
    
    def get_events(self, topic):
        return [e for e in self.events if e.topic == topic]
```

---

## Assertions

```python
# Standard Assertions
assert result.status == "success"
assert result.duration < 1000
assert len(result.data) > 0

# Custom Assertions
assert_agent_registered(agent_id)
assert_task_completed(task_id)
assert_event_published(event_bus, "task.completed")
assert_knowledge_stored(memory, key, value)
```

---

## Test Daten

```yaml
Test Data:
  Strategy: Factory Pattern
  
  Factories:
    - AgentFactory
    - TaskFactory
    - EventFactory
    - KnowledgeFactory
  
  Fixtures:
    - Static fixtures in JSON/YAML
    - Dynamic fixtures via factories
```

---

## Dokumente

```
tests/
├── README.md
├── conftest.py
├── unit/
├── integration/
├── e2e/
├── fixtures/
└── helpers/
```

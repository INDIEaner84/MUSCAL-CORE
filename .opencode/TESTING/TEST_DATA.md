# MUSCAL Test Data Management

## Zweck

Management von Testdaten für reproduzierbare Tests.

---

## Strategie

```yaml
Test Data Strategy:
  Primary: Fixtures (JSON/YAML)
  Secondary: Factories (Python)
  Database: Seed data + fixtures
  
  Principles:
    - Each test is independent
    - Tests create own data
    - Cleanup after each test
    - No shared state
```

---

## Fixtures

### Agent Fixtures

```yaml
# fixtures/agents.yaml
agents:
  - id: AGT-001
    name: TestCoreAgent
    type: core
    status: active
    version: 1.0.0
    capabilities:
      - testing
      - analysis
  
  - id: AGT-002
    name: TestGovernanceAgent
    type: governance
    status: active
    version: 1.0.0
    capabilities:
      - security
      - compliance
```

### Task Fixtures

```yaml
# fixtures/tasks.yaml
tasks:
  - id: task-001
    name: Test Task
    type: implementation
    priority: high
    status: pending
    assigned_to: AGT-001
  
  - id: task-002
    name: Urgent Task
    type: bugfix
    priority: critical
    status: in_progress
    assigned_to: AGT-002
```

### Event Fixtures

```yaml
# fixtures/events.yaml
events:
  - id: evt-001
    type: event
    topic: task.created
    source: AGT-004
    payload:
      event: task_created
      data:
        task_id: task-001
  
  - id: evt-002
    type: error
    topic: agent.error
    source: AGT-001
    payload:
      error:
        code: TEST_FAILED
        message: "Test failed"
```

---

## Factories

```python
# factories/agent_factory.py
class AgentFactory:
    _id_counter = 0
    
    @classmethod
    def create(cls, **kwargs):
        cls._id_counter += 1
        
        defaults = {
            "id": f"AGT-{cls._id_counter:03d}",
            "name": f"TestAgent{cls._id_counter}",
            "type": "core",
            "status": "active",
            "version": "1.0.0",
            "capabilities": ["testing"]
        }
        
        defaults.update(kwargs)
        return Agent(**defaults)

# factories/task_factory.py
class TaskFactory:
    _id_counter = 0
    
    @classmethod
    def create(cls, **kwargs):
        cls._id_counter += 1
        
        defaults = {
            "id": f"task-{cls._id_counter:03d}",
            "name": f"TestTask{cls._id_counter}",
            "type": "implementation",
            "priority": "medium",
            "status": "pending"
        }
        
        defaults.update(kwargs)
        return Task(**defaults)
```

---

## Database Fixtures

```python
# fixtures/database.py
@pytest.fixture
def db_session():
    """Create a fresh database session for each test."""
    session = create_test_session()
    yield session
    session.rollback()
    session.close()

@pytest.fixture
def sample_agents(db_session):
    """Create sample agents in database."""
    agents = [
        Agent(id="AGT-001", name="Agent1", type="core"),
        Agent(id="AGT-002", name="Agent2", type="governance")
    ]
    db_session.add_all(agents)
    db_session.commit()
    return agents
```

---

## Test Data Generatoren

```python
# generators/data_generator.py
class TestDataGenerator:
    @staticmethod
    def generate_agent():
        return {
            "id": f"AGT-{random.randint(100, 999)}",
            "name": f"Agent-{uuid.uuid4().hex[:8]}",
            "type": random.choice(["core", "governance", "business", "ops"]),
            "status": "active",
            "version": "1.0.0"
        }
    
    @staticmethod
    def generate_task():
        return {
            "id": f"task-{uuid.uuid4().hex[:8]}",
            "name": f"Task-{uuid.uuid4().hex[:8]}",
            "type": random.choice(["implementation", "testing", "documentation"]),
            "priority": random.choice(["low", "medium", "high", "critical"]),
            "status": "pending"
        }
```

---

## Cleanup

```python
# conftest.py
@pytest.fixture(autouse=True)
def cleanup():
    """Cleanup after each test."""
    yield
    # Cleanup code here
    cleanup_database()
    cleanup_files()
    cleanup_events()
```

---

## Dokumente

```
testing/
├── TEST_DATA.md
├── fixtures/
│   ├── agents.yaml
│   ├── tasks.yaml
│   └── events.yaml
├── factories/
│   ├── agent_factory.py
│   └── task_factory.py
└── generators/
    └── data_generator.py
```

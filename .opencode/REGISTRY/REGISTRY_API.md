# MUSCAL Registry API Specification

## Zweck

API-Spezifikation für die Agent Registry.

---

## Endpoints

### Agent Operations

```yaml
GET /api/registry/agents
  Description: Alle Agenten auflisten
  Query Parameters:
    type: core/governance/business/ops
    status: active/inactive/maintenance
    capability: {capability}
  Response: AgentList

GET /api/registry/agents/{agent_id}
  Description: Einzelnen Agent abrufen
  Response: Agent

POST /api/registry/agents
  Description: Neuen Agent registrieren
  Body: AgentDefinition
  Response: Agent

PUT /api/registry/agents/{agent_id}
  Description: Agent aktualisieren
  Body: AgentUpdate
  Response: Agent

DELETE /api/registry/agents/{agent_id}
  Description: Agent deregistrieren
  Response: Status
```

### Lookup Operations

```yaml
GET /api/registry/lookup
  Description: Agenten nach Kriterien suchen
  Query Parameters:
    query: {suchbegriff}
    type: {typ}
    capability: {fertigkeit}
  Response: AgentList

GET /api/registry/lookup/by-capability/{capability}
  Description: Alle Agenten mit bestimmter Fertigkeit
  Response: AgentList

GET /api/registry/lookup/by-type/{type}
  Description: Alle Agenten eines Typs
  Response: AgentList
```

### Statistics

```yaml
GET /api/registry/statistics
  Description: Registry Statistiken
  Response: Statistics

GET /api/registry/statistics/by-type
  Description: Statistiken nach Typ
  Response: TypeStatistics

GET /api/registry/statistics/by-capability
  Description: Statistiken nach Fertigkeit
  Response: CapabilityStatistics
```

---

## Request/Response Schemas

### Agent

```yaml
Agent:
  type: object
  required:
    - ID
    - Name
    - Type
    - Status
    - Version
    - Capabilities
  properties:
    ID:
      type: string
      pattern: "AGT-[0-9]{3}"
    Name:
      type: string
    Type:
      type: string
      enum: [core, governance, business, ops]
    Status:
      type: string
      enum: [active, inactive, maintenance]
    Version:
      type: string
      pattern: "[0-9]+\\.[0-9]+\\.[0-9]+"
    Capabilities:
      type: array
      items:
        type: string
    Documentation:
      type: string
    CreatedAt:
      type: string
      format: date-time
    UpdatedAt:
      type: string
      format: date-time
```

### AgentList

```yaml
AgentList:
  type: object
  properties:
    agents:
      type: array
      items:
        $ref: '#/Agent'
    total:
      type: integer
    page:
      type: integer
    pageSize:
      type: integer
```

---

## Fehlerbehandlung

```yaml
Error Response:
  type: object
  properties:
    error:
      type: object
      properties:
        code:
          type: string
        message:
          type: string
        details:
          type: array
          items:
            type: object
            properties:
              field:
                type: string
              message:
                type: string
```

### Fehlercodes

| Code | Beschreibung |
|------|--------------|
| AGENT_NOT_FOUND | Agent nicht gefunden |
| AGENT_EXISTS | Agent bereits registriert |
| INVALID_DATA | Ungültige Daten |
| UNAUTHORIZED | Keine Berechtigung |
| INTERNAL_ERROR | Interner Fehler |

---

## Beispiele

### Agent registrieren

```bash
curl -X POST http://localhost:8080/api/registry/agents \
  -H "Content-Type: application/json" \
  -d '{
    "Name": "MeinAgent",
    "Type": "core",
    "Version": "1.0.0",
    "Capabilities": ["capability1", "capability2"],
    "Documentation": "path/to/docs.md"
  }'
```

### Agenten auflisten

```bash
curl http://localhost:8080/api/registry/agents?type=core
```

### Nach Fertigkeit suchen

```bash
curl http://localhost:8080/api/registry/lookup/by-capability/security_scanning
```

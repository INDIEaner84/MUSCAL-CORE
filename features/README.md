# Features — MUSCAL CORE Plugin-Verzeichnis

Hier entstehen alle Erweiterungen.

## Struktur

```
features/
├── mkc/       # Plugins für die Compiler-Pipeline
├── bridge/    # Plugins für Tool-Mapping
├── memory/    # Plugins für Persistenz
└── runtime/   # Plugins für Laufzeit-Infrastruktur
```

## Plugin-Contract

```python
class Plugin:
    name: str
    def register(self, hooks: dict): ...
    def execute(self, context: dict): ...
```

## Wichtige Dateien

- `spec/PLUGIN_API.md` — Vollständige SDK-Dokumentation
- `plugin_registry.py` — Hook-Registry
- `plugin_loader.py` — Plugin-Discovery + Safety

## 5 Referenz-Plugins

| Plugin | Datei | Monitor |
|--------|-------|---------|
| Audit Logger | `features/mkc/audit_plugin.py` | Laufzeit-Messung |
| Execution Trace | `features/mkc/trace_plugin.py` | Pipeline-Trace |
| Confidence Metrics | `features/mkc/confidence_plugin.py` | Confidence-Verlauf |
| RAG Enrichment | `features/mkc/rag_enrich_plugin.py` | Metadaten-Anreicherung |
| Health Monitor | `features/runtime/health_monitor.py` | Fehlererkennung |

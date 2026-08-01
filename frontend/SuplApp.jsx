import { useEffect, useState, useCallback } from "react";
import ModeToggle from "./ModeToggle";
import SemanticOverlay from "./SemanticOverlay";
import SemanticGraphView from "./SemanticGraphView";
import SuplExecutionView from "./SuplExecutionView";
import useSuplWebSocket from "./useSuplWebSocket";

const API_BASE = "http://localhost:8000";

const containerStyle = {
  border: "1px solid #4a90d9",
  borderRadius: "8px",
  padding: "16px",
  margin: "12px 0",
  background: "#1a1a2e",
  color: "#e0e0e0",
  fontFamily: "monospace",
};

const headerStyle = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  marginBottom: "12px",
};

const selectStyle = {
  background: "#2a2a2a",
  border: "1px solid #555",
  color: "#e0e0e0",
  padding: "6px 10px",
  borderRadius: "4px",
  fontSize: "13px",
};

function ConnectionBadge({ state, resyncRequired }) {
  if (resyncRequired) {
    return (
      <span
        style={{
          display: "inline-block",
          padding: "2px 8px",
          borderRadius: "10px",
          background: "#e74c3c44",
          color: "#e74c3c",
          border: "1px solid #e74c3c",
          fontSize: "10px",
          fontWeight: "bold",
          cursor: "pointer",
        }}
        title="Resync required - click to reconnect"
        onClick={() => window.location.reload()}
      >
        RESYNC
      </span>
    );
  }
  const badges = {
    CONNECTED: { bg: "#2ecc7144", color: "#2ecc71", label: "LIVE" },
    RECONNECTING: { bg: "#f39c1244", color: "#f39c12", label: "RECON" },
    DISCONNECTED: { bg: "#e74c3c44", color: "#e74c3c", label: "OFF" },
    RESYNCING: { bg: "#e74c3c44", color: "#e74c3c", label: "SYNC" },
  };
  const b = badges[state] || badges.DISCONNECTED;
  return (
    <span
      style={{
        display: "inline-block",
        padding: "2px 8px",
        borderRadius: "10px",
        background: b.bg,
        color: b.color,
        border: `1px solid ${b.color}`,
        fontSize: "10px",
        fontWeight: "bold",
      }}
    >
      {b.label}
    </span>
  );
}

function NativeView({ projection, executionStatus, provenance, onExecute }) {
  if (!projection) return null;
  const caps = projection.capabilities || [];
  const actions = projection.actions || [];

  return (
    <div>
      <div style={{ fontWeight: "bold", fontSize: "14px", marginBottom: "8px" }}>
        {projection.application_name || projection.application_id}
      </div>
      {caps.map((cap, ci) => (
        <div
          key={cap.id || ci}
          style={{
            border: "1px solid #3a3a3a",
            borderRadius: "4px",
            padding: "8px",
            margin: "6px 0",
          }}
        >
          <div style={{ fontWeight: "bold", color: "#3498db", fontSize: "12px" }}>
            {cap.name || cap.id}
          </div>
          {actions
            .filter((a) => a.capability_id === cap.id)
            .map((act, ai) => (
              <div key={act.id || ai} style={{ marginTop: "4px" }}>
                <span style={{ color: "#2ecc71", fontSize: "12px" }}>
                  {act.name || act.id}
                </span>
                <button
                  onClick={() => onExecute(act.id, {})}
                  style={{
                    marginLeft: "8px",
                    background: "#4a90d9",
                    color: "#fff",
                    border: "none",
                    padding: "2px 10px",
                    borderRadius: "3px",
                    cursor: "pointer",
                    fontSize: "11px",
                  }}
                >
                  Run
                </button>
              </div>
            ))}
        </div>
      ))}
    </div>
  );
}

export default function SuplApp() {
  const [apps, setApps] = useState([]);
  const [selectedAppId, setSelectedAppId] = useState(null);
  const [mode, setMode] = useState("native");
  const [projection, setProjection] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [executionStatus, setExecutionStatus] = useState("READY");
  const [executions, setExecutions] = useState([]);
  const [provenances, setProvenances] = useState({});

  const { connectionState, events, currentSeq, resyncRequired, resync } =
    useSuplWebSocket();

  useEffect(() => {
    fetch(`${API_BASE}/api/supl/apps`)
      .then((r) => r.json())
      .then((data) => {
        const list = data.apps || data || [];
        setApps(list);
        if (list.length > 0 && !selectedAppId) {
          setSelectedAppId(list[0].id || list[0].app_id);
        }
      })
      .catch((e) => setError("Failed to load apps: " + e.message));
  }, []);

  useEffect(() => {
    if (!selectedAppId) return;
    setLoading(true);
    setError(null);
    fetch(`${API_BASE}/api/supl/projection/${selectedAppId}?mode=${mode}`)
      .then((r) => r.json())
      .then((data) => {
        setProjection(data.projection || data);
        setLoading(false);
      })
      .catch((e) => {
        setError("Failed to load projection: " + e.message);
        setLoading(false);
      });
  }, [selectedAppId, mode]);

  const handleExecute = useCallback(
    (actionId, params) => {
      if (!selectedAppId) return;
      setExecutionStatus("REQUESTED");
      fetch(`${API_BASE}/api/supl/apps/${selectedAppId}/action`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: actionId, parameters: params }),
      })
        .then((r) => r.json())
        .then((data) => {
          const status = data.status || data.result || "EXECUTED";
          setExecutionStatus(status === "success" ? "EXECUTED" : status);
          setExecutions((prev) => [
            {
              interaction_id: data.interaction_id || crypto.randomUUID(),
              action_id: actionId,
              status: data.status || "EXECUTED",
              pattern: data.pattern,
            },
            ...prev.slice(0, 49),
          ]);
          if (data.interaction_id && data.provenance) {
            setProvenances((prev) => ({
              ...prev,
              [data.interaction_id]: data.provenance,
            }));
          }
        })
        .catch((e) => {
          setExecutionStatus("FAILED");
          setExecutions((prev) => [
            {
              interaction_id: crypto.randomUUID(),
              action_id: actionId,
              status: "FAILED",
              error: e.message,
            },
            ...prev.slice(0, 49),
          ]);
        });
    },
    [selectedAppId]
  );

  const handleModeChange = useCallback(
    (newMode) => {
      setMode(newMode);
      setExecutionStatus("READY");
    },
    []
  );

  const handleAppChange = useCallback((e) => {
    setSelectedAppId(e.target.value);
    setExecutionStatus("READY");
    setProjection(null);
    setExecutions([]);
    setProvenances({});
  }, []);

  const filteredEvents = events.filter(
    (e) => !selectedAppId || e.app_id === selectedAppId || !e.app_id
  );

  return (
    <div style={containerStyle}>
      <div style={headerStyle}>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <strong style={{ fontSize: "14px" }}>M-SUPL</strong>
          <select
            style={selectStyle}
            value={selectedAppId || ""}
            onChange={handleAppChange}
          >
            {apps.map((app) => (
              <option key={app.id || app.app_id} value={app.id || app.app_id}>
                {app.name || app.id || app.app_id}
              </option>
            ))}
          </select>
          <ModeToggle mode={mode} onChange={handleModeChange} />
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <ConnectionBadge state={connectionState} resyncRequired={resyncRequired} />
          <span style={{ fontSize: "10px", color: "#666" }}>
            seq: {currentSeq}
          </span>
        </div>
      </div>

      {error && (
        <div
          style={{
            color: "#e74c3c",
            fontSize: "12px",
            marginBottom: "8px",
            padding: "6px",
            border: "1px solid #e74c3c",
            borderRadius: "4px",
          }}
        >
          {error}
        </div>
      )}

      {loading && (
        <div style={{ color: "#888", fontSize: "12px" }}>Loading projection...</div>
      )}

      {!loading && mode === "native" && (
        <NativeView
          projection={projection}
          executionStatus={executionStatus}
          provenance={provenances[executions[0]?.interaction_id]}
          onExecute={handleExecute}
        />
      )}

      {!loading && mode === "overlay" && (
        <SemanticOverlay
          projection={projection}
          executionStatus={executionStatus}
          provenance={provenances[executions[0]?.interaction_id]}
          onExecute={handleExecute}
        />
      )}

      {!loading && mode === "graph_native" && (
        <SemanticGraphView
          projection={projection}
          events={filteredEvents}
          onExecute={handleExecute}
        />
      )}

      {!loading && executions.length > 0 && (
        <SuplExecutionView executions={executions} provenances={provenances} />
      )}

      <div style={{ marginTop: "8px", fontSize: "10px", color: "#555" }}>
        Events received: {events.length} | Mode: {mode.toUpperCase()} |
        App: {selectedAppId || "-"}
      </div>
    </div>
  );
}

import { useState } from "react";

const containerStyle = {
  border: "1px solid #444",
  borderRadius: "8px",
  padding: "16px",
  margin: "8px 0",
  background: "#1e1e1e",
  color: "#e0e0e0",
  fontFamily: "monospace",
  fontSize: "13px",
  maxWidth: "480px",
};

const labelStyle = { color: "#888", fontSize: "11px", marginRight: "8px" };
const valueStyle = { color: "#e0e0e0" };
const capStyle = {
  border: "1px solid #3a3a3a",
  borderRadius: "4px",
  padding: "8px",
  margin: "6px 0",
};
const inputStyle = {
  background: "#2a2a2a",
  border: "1px solid #555",
  color: "#e0e0e0",
  padding: "4px 8px",
  borderRadius: "3px",
  width: "60px",
  marginRight: "4px",
};
const btnStyle = {
  background: "#4a90d9",
  color: "#fff",
  border: "none",
  padding: "6px 14px",
  borderRadius: "4px",
  cursor: "pointer",
  marginTop: "6px",
};

function StatusBadge({ status }) {
  const colors = {
    REQUESTED: "#f39c12",
    AUTHORIZED: "#3498db",
    EXECUTING: "#2ecc71",
    EXECUTED: "#27ae60",
    VERIFIED: "#1abc9c",
    FAILED: "#e74c3c",
    REJECTED: "#e67e22",
    INCONSISTENT: "#e74c3c",
    READY: "#2ecc71",
  };
  const color = colors[status] || "#888";
  return (
    <span
      style={{
        display: "inline-block",
        padding: "2px 8px",
        borderRadius: "10px",
        background: color + "22",
        color: color,
        border: `1px solid ${color}`,
        fontSize: "11px",
        fontWeight: "bold",
      }}
    >
      {status}
    </span>
  );
}

export default function SemanticOverlay({
  projection,
  executionStatus,
  provenance,
  onExecute,
}) {
  const [params, setParams] = useState({});

  if (!projection) {
    return (
      <div style={containerStyle}>
        <div style={{ color: "#888" }}>No projection loaded</div>
      </div>
    );
  }

  const capabilities = projection.capabilities || [];
  const actions = projection.actions || [];
  const appState = projection.state || {};
  const lifecycle = projection.lifecycle || "unknown";

  const handleParamChange = (capId, actionId, paramName, value) => {
    setParams((prev) => ({
      ...prev,
      [`${capId}:${actionId}`]: {
        ...prev[`${capId}:${actionId}`],
        [paramName]: value,
      },
    }));
  };

  const handleExecute = (capId, actionId) => {
    const actionParams = params[`${capId}:${actionId}`] || {};
    if (onExecute) {
      onExecute(actionId, actionParams);
    }
  };

  return (
    <div style={containerStyle}>
      <div style={{ fontWeight: "bold", fontSize: "15px", marginBottom: "8px" }}>
        {projection.application_name || projection.application_id}
        <span style={{ marginLeft: "8px" }}>
          <StatusBadge status={executionStatus || "READY"} />
        </span>
      </div>

      <div style={{ marginBottom: "12px" }}>
        <span style={labelStyle}>ID:</span>
        <span style={valueStyle}>{projection.application_id}</span>
        <br />
        <span style={labelStyle}>Version:</span>
        <span style={valueStyle}>{projection.application_version || "-"}</span>
        <br />
        <span style={labelStyle}>Lifecycle:</span>
        <span style={valueStyle}>{lifecycle}</span>
      </div>

      {capabilities.length > 0 && (
        <div>
          <div style={{ color: "#888", fontSize: "11px", marginBottom: "4px" }}>
            CAPABILITIES
          </div>
          {capabilities.map((cap, ci) => {
            const capActions = actions.filter(
              (a) => a.capability_id === cap.id || a.capability_id === cap.id
            );
            return (
              <div key={cap.id || ci} style={capStyle}>
                <div style={{ fontWeight: "bold", fontSize: "13px" }}>
                  {cap.name || cap.id}
                </div>
                {cap.description && (
                  <div style={{ color: "#aaa", fontSize: "11px", margin: "2px 0" }}>
                    {cap.description}
                  </div>
                )}
                {capActions.map((act, ai) => (
                  <div key={act.id || ai} style={{ marginTop: "6px" }}>
                    <div style={{ color: "#ccc", fontSize: "12px" }}>
                      {act.name || act.id}
                    </div>
                    {act.parameter_ids &&
                      act.parameter_ids.map((pid) => {
                        const paramDef = (projection.parameters || []).find(
                          (p) => p.id === pid || p.name === pid
                        );
                        return (
                          <div key={pid} style={{ margin: "4px 0" }}>
                            <span style={labelStyle}>{paramDef?.name || pid}:</span>
                            <input
                              style={inputStyle}
                              placeholder={paramDef?.type || "text"}
                              onChange={(e) =>
                                handleParamChange(cap.id, act.id, pid, e.target.value)
                              }
                            />
                          </div>
                        );
                      })}
                    <button
                      style={btnStyle}
                      onClick={() => handleExecute(cap.id, act.id)}
                    >
                      Execute
                    </button>
                  </div>
                ))}
              </div>
            );
          })}
        </div>
      )}

      {Object.keys(appState).length > 0 && (
        <div style={{ marginTop: "12px" }}>
          <div style={{ color: "#888", fontSize: "11px", marginBottom: "4px" }}>
            STATE
          </div>
          {Object.entries(appState).map(([k, v]) => (
            <div key={k}>
              <span style={labelStyle}>{k}:</span>
              <span style={valueStyle}>
                {v?.value !== undefined ? String(v.value) : String(v)}
              </span>
            </div>
          ))}
        </div>
      )}

      {provenance && (
        <div style={{ marginTop: "12px", borderTop: "1px solid #333", paddingTop: "8px" }}>
          <div style={{ color: "#888", fontSize: "11px", marginBottom: "4px" }}>
            PROVENANCE
          </div>
          {provenance.interaction_id && (
            <div>
              <span style={labelStyle}>Interaction:</span>
              <span style={valueStyle}>{provenance.interaction_id.substring(0, 12)}...</span>
            </div>
          )}
          {provenance.execution_id && (
            <div>
              <span style={labelStyle}>Execution:</span>
              <span style={valueStyle}>{provenance.execution_id.substring(0, 12)}...</span>
            </div>
          )}
          {provenance.receipt_id && (
            <div>
              <span style={labelStyle}>Receipt:</span>
              <span style={valueStyle}>{provenance.receipt_id.substring(0, 12)}...</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

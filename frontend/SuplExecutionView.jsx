const containerStyle = {
  border: "1px solid #444",
  borderRadius: "8px",
  padding: "16px",
  margin: "8px 0",
  background: "#1e1e1e",
  color: "#e0e0e0",
  fontFamily: "monospace",
  fontSize: "13px",
  maxHeight: "300px",
  overflowY: "auto",
};

const labelStyle = { color: "#888", fontSize: "11px", marginRight: "8px" };
const valueStyle = { color: "#e0e0e0" };

function StatusDot({ status }) {
  const colors = {
    REQUESTED: "#f39c12",
    AUTHORIZED: "#3498db",
    EXECUTING: "#2ecc71",
    EXECUTED: "#27ae60",
    VERIFIED: "#1abc9c",
    FAILED: "#e74c3c",
    REJECTED: "#e67e22",
    INCONSISTENT: "#e74c3c",
  };
  const color = colors[status] || "#888";
  return (
    <span
      style={{
        display: "inline-block",
        width: "8px",
        height: "8px",
        borderRadius: "50%",
        background: color,
        marginRight: "6px",
        flexShrink: 0,
      }}
    />
  );
}

export default function SuplExecutionView({ executions, provenances }) {
  if (!executions || executions.length === 0) {
    return (
      <div style={containerStyle}>
        <div style={{ color: "#888", fontSize: "11px" }}>No executions yet</div>
      </div>
    );
  }

  return (
    <div style={containerStyle}>
      <div style={{ color: "#888", fontSize: "11px", marginBottom: "8px" }}>
        EXECUTION HISTORY
      </div>
      {executions.map((ex, i) => {
        const prov = provenances ? provenances[ex.interaction_id] : null;
        return (
          <div
            key={ex.interaction_id || i}
            style={{
              borderBottom: "1px solid #333",
              padding: "8px 0",
            }}
          >
            <div style={{ display: "flex", alignItems: "center" }}>
              <StatusDot status={ex.status} />
              <span style={{ fontWeight: "bold", fontSize: "12px" }}>
                {ex.action_id?.substring(0, 20) || ex.action_name || "action"}
              </span>
            </div>
            <div style={{ marginTop: "4px", fontSize: "11px" }}>
              <span style={labelStyle}>Status:</span>
              <span style={valueStyle}>{ex.status}</span>
              {ex.pattern && (
                <>
                  <br />
                  <span style={labelStyle}>Pattern:</span>
                  <span style={valueStyle}>{ex.pattern}</span>
                </>
              )}
            </div>
            {prov && (
              <div style={{ marginTop: "4px", fontSize: "10px", color: "#777" }}>
                <span style={labelStyle}>Exec:</span>
                <span>{prov.execution_id?.substring(0, 12) || "-"}..</span>
                <span style={{ marginLeft: "8px", ...labelStyle }}>Rec:</span>
                <span>{prov.receipt_id?.substring(0, 12) || "-"}..</span>
                {prov.verification_id && (
                  <>
                    <span style={{ marginLeft: "8px", ...labelStyle }}>Ver:</span>
                    <span>{prov.verification_id.substring(0, 12)}..</span>
                  </>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

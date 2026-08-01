const MODES = ["native", "overlay", "graph_native"];

const MODE_LABELS = {
  native: "NATIVE",
  overlay: "OVERLAY",
  graph_native: "GRAPH",
};

const MODE_COLORS = {
  native: "#4a90d9",
  overlay: "#7b68ee",
  graph_native: "#2ecc71",
};

const btnStyle = (mode, current) => ({
  padding: "6px 14px",
  margin: "0 4px",
  border: current === mode ? "2px solid #fff" : "1px solid #555",
  borderRadius: "4px",
  background: current === mode ? MODE_COLORS[mode] : "#2a2a2a",
  color: "#fff",
  cursor: "pointer",
  fontWeight: current === mode ? "bold" : "normal",
  fontSize: "12px",
});

export default function ModeToggle({ mode, onChange }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
      {MODES.map((m) => (
        <button
          key={m}
          style={btnStyle(m, mode)}
          onClick={() => onChange(m)}
          title={`Switch to ${MODE_LABELS[m]} mode`}
        >
          {MODE_LABELS[m]}
        </button>
      ))}
    </div>
  );
}

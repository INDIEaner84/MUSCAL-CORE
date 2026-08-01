import { useState } from "react";

const NODE_TYPES = {
  APPLICATION: { fill: "#e74c3c", r: 30 },
  CAPABILITY: { fill: "#3498db", r: 22 },
  ACTION: { fill: "#2ecc71", r: 18 },
  PARAMETER: { fill: "#f39c12", r: 14 },
  STATE: { fill: "#9b59b6", r: 16 },
  EVENT: { fill: "#1abc9c", r: 12 },
};

const containerStyle = {
  border: "1px solid #444",
  borderRadius: "8px",
  padding: "16px",
  margin: "8px 0",
  background: "#1e1e1e",
  color: "#e0e0e0",
  fontFamily: "monospace",
  overflow: "hidden",
};

function layoutNodes(projection, svgW, svgH) {
  const nodes = [];
  const edges = [];

  if (!projection) return { nodes, edges };

  const cx = svgW / 2;
  const cy = svgH / 2;

  const appNode = {
    id: projection.application_id || "app",
    label: projection.application_name || projection.application_id,
    type: "APPLICATION",
    x: cx,
    y: 60,
  };
  nodes.push(appNode);

  const caps = projection.capabilities || [];
  const capRadius = 120;
  const capAngleStep = (2 * Math.PI) / Math.max(caps.length, 1);

  caps.forEach((cap, ci) => {
    const angle = capAngleStep * ci - Math.PI / 2;
    const capNode = {
      id: cap.id,
      label: cap.name || cap.id,
      type: "CAPABILITY",
      x: cx + capRadius * Math.cos(angle),
      y: 120 + capRadius * Math.sin(angle),
    };
    nodes.push(capNode);
    edges.push({ from: appNode.id, to: capNode.id, label: "exposes" });

    const actions = (projection.actions || []).filter(
      (a) => a.capability_id === cap.id
    );
    const actRadius = 70;
    const actAngleStep = (2 * Math.PI) / Math.max(actions.length, 1);

    actions.forEach((act, ai) => {
      const aAngle = actAngleStep * ai + angle;
      const actNode = {
        id: act.id,
        label: act.name || act.id,
        type: "ACTION",
        x: capNode.x + actRadius * Math.cos(aAngle),
        y: capNode.y + actRadius * Math.sin(aAngle),
      };
      nodes.push(actNode);
      edges.push({ from: capNode.id, to: actNode.id, label: "has" });

      if (act.parameter_ids) {
        act.parameter_ids.forEach((pid, pi) => {
          const param = (projection.parameters || []).find(
            (p) => p.id === pid || p.name === pid
          );
          if (param) {
            const pNode = {
              id: param.id || pid,
              label: param.name || pid,
              type: "PARAMETER",
              x: actNode.x + 60 + pi * 20,
              y: actNode.y + 30 + pi * 30,
            };
            nodes.push(pNode);
            edges.push({ from: actNode.id, to: pNode.id, label: "requires" });
          }
        });
      }
    });
  });

  const appState = projection.state || {};
  const stateKeys = Object.keys(appState);
  stateKeys.forEach((sk, si) => {
    const stateNode = {
      id: `state:${sk}`,
      label: `${sk}=${appState[sk]?.value !== undefined ? appState[sk].value : appState[sk]}`,
      type: "STATE",
      x: 60 + si * 20,
      y: 350,
    };
    nodes.push(stateNode);
    edges.push({ from: appNode.id, to: stateNode.id, label: "state" });
  });

  return { nodes, edges };
}

export default function SemanticGraphView({
  projection,
  events,
  onNodeClick,
  onExecute,
}) {
  const [selectedNode, setSelectedNode] = useState(null);
  const SVG_W = 800;
  const SVG_H = 500;

  const { nodes, edges } = layoutNodes(projection, SVG_W, SVG_H);

  const handleNodeClick = (node) => {
    setSelectedNode(node);
    if (onNodeClick) onNodeClick(node);
  };

  return (
    <div style={containerStyle}>
      <svg width={SVG_W} height={SVG_H} style={{ display: "block" }}>
        <defs>
          <marker id="arrowhead" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
            <polygon points="0 0, 8 3, 0 6" fill="#666" />
          </marker>
        </defs>
        {edges.map((e, i) => {
          const fromNode = nodes.find((n) => n.id === e.from);
          const toNode = nodes.find((n) => n.id === e.to);
          if (!fromNode || !toNode) return null;
          return (
            <g key={`edge-${i}`}>
              <line
                x1={fromNode.x}
                y1={fromNode.y}
                x2={toNode.x}
                y2={toNode.y}
                stroke="#555"
                strokeWidth="1.5"
                markerEnd="url(#arrowhead)"
              />
              <text
                x={(fromNode.x + toNode.x) / 2}
                y={(fromNode.y + toNode.y) / 2 - 6}
                fill="#777"
                fontSize="9"
                textAnchor="middle"
              >
                {e.label}
              </text>
            </g>
          );
        })}
        {nodes.map((n) => {
          const typeDef = NODE_TYPES[n.type] || NODE_TYPES.APPLICATION;
          const isSelected = selectedNode && selectedNode.id === n.id;
          return (
            <g key={n.id} onClick={() => handleNodeClick(n)} style={{ cursor: "pointer" }}>
              <circle
                cx={n.x}
                cy={n.y}
                r={typeDef.r}
                fill={isSelected ? "#fff" : typeDef.fill}
                stroke={isSelected ? typeDef.fill : "#333"}
                strokeWidth={isSelected ? 2 : 1}
                opacity={isSelected ? 1 : 0.85}
              />
              <text
                x={n.x}
                y={n.y + typeDef.r + 12}
                fill="#ccc"
                fontSize="9"
                textAnchor="middle"
              >
                {n.label && n.label.length > 20
                  ? n.label.substring(0, 18) + ".."
                  : n.label || n.id}
              </text>
            </g>
          );
        })}
      </svg>

      {selectedNode && selectedNode.type === "ACTION" && onExecute && (
        <div style={{ marginTop: "8px", textAlign: "center" }}>
          <button
            onClick={() => onExecute(selectedNode.id, {})}
            style={{
              background: "#2ecc71",
              color: "#fff",
              border: "none",
              padding: "6px 16px",
              borderRadius: "4px",
              cursor: "pointer",
              fontWeight: "bold",
            }}
          >
            Execute {selectedNode.label || selectedNode.id}
          </button>
        </div>
      )}

      {events && events.length > 0 && (
        <div style={{ marginTop: "12px", borderTop: "1px solid #333", paddingTop: "8px" }}>
          <div style={{ color: "#888", fontSize: "11px", marginBottom: "4px" }}>
            RECENT EVENTS
          </div>
          {events.slice(-5).map((evt, i) => (
            <div key={i} style={{ fontSize: "11px", color: "#aaa" }}>
              {evt.topic || evt.type}: {evt.status || ""}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

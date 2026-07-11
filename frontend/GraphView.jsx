import { useEffect, useState } from "react";

export default function GraphView() {
  const [graph, setGraph] = useState({nodes: [], edges: []});

  useEffect(() => {
    fetch("/graph")
      .then(r => r.json())
      .then(setGraph);
  }, []);

  return (
    <div>
      <h1>MUSCAL Graph Observatory</h1>

      <svg width="800" height="600">
        {graph.nodes.map(n => (
          <circle key={n.id} cx={Math.random()*800} cy={Math.random()*600} r={5} />
        ))}
      </svg>
    </div>
  );
}

import { useState } from "react";

export default function MetaExplain() {
  const [nodeId, setNodeId] = useState("");
  const [data, setData] = useState(null);

  const run = async () => {
    const res = await fetch(`/meta-explain/${nodeId}`);
    setData(await res.json());
  };

  return (
    <div>
      <h1>Meta-Reasoning</h1>

      <input onChange={e => setNodeId(e.target.value)} />
      <button onClick={run}>Analyze</button>

      {data && (
        <div>
          <h2>Critique</h2>
          <pre>{JSON.stringify(data.critique, null, 2)}</pre>

          <h2>Refined Explanation</h2>
          <pre>{data.refined_explanation}</pre>
        </div>
      )}
    </div>
  );
}

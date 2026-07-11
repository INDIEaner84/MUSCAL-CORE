import { useState } from "react";

export default function Explain() {
  const [nodeId, setNodeId] = useState("");
  const [data, setData] = useState(null);

  const run = async () => {
    const res = await fetch(`/explain/${nodeId}`);
    setData(await res.json());
  };

  return (
    <div>
      <h1>Decision Autopsy</h1>

      <input onChange={e => setNodeId(e.target.value)} />
      <button onClick={run}>Explain</button>

      {data && (
        <pre>{JSON.stringify(data, null, 2)}</pre>
      )}
    </div>
  );
}

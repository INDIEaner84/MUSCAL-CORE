import { useState } from "react";

export default function Replay({nodeId}) {
  const [path, setPath] = useState([]);

  const load = async () => {
    const res = await fetch(`/replay/${nodeId}`);
    setPath(await res.json());
  };

  return (
    <div>
      <button onClick={load}>Replay</button>

      {path.map((p, i) => (
        <div key={i}>
          [{p.type}] {JSON.stringify(p.payload)}
        </div>
      ))}
    </div>
  );
}

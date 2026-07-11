import { useEffect, useState } from "react";
import NodePanel from "./NodePanel";
import TraceViewer from "./TraceViewer";
import TaskBox from "./TaskBox";

export default function Dashboard() {
  const [nodes, setNodes] = useState([]);
  const [logs, setLogs] = useState([]);

  useEffect(() => {
    fetch("/nodes")
      .then(res => res.json())
      .then(setNodes);

    const ws = new WebSocket("ws://localhost:8000/stream");

    ws.onmessage = (msg) => {
      setLogs(prev => [...prev, msg.data]);
    };
  }, []);

  return (
    <div>
      <h1>MUSCAL Control Plane</h1>

      <h2>Nodes</h2>
      <NodePanel nodes={nodes} />

      <h2>Trace</h2>
      <TraceViewer logs={logs} />

      <TaskBox />
    </div>
  );
}

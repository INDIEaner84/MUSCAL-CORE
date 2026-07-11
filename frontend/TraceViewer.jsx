export default function TraceViewer({logs}) {
  return (
    <div style={{fontFamily: "monospace"}}>
      {logs.map((l, i) => (
        <div key={i}>[{i}] {l}</div>
      ))}
    </div>
  );
}

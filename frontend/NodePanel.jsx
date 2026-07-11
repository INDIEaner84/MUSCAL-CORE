export default function NodePanel({nodes}) {
  return (
    <div>
      {nodes.map(n => (
        <div key={n.id}>
          🟢 Node: {n.id}
        </div>
      ))}
    </div>
  );
}

import { useState } from "react";

export default function TaskBox() {
  const [input, setInput] = useState("");

  const send = async () => {
    await fetch("/task", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({input})
    });
  };

  return (
    <div>
      <input onChange={e => setInput(e.target.value)} />
      <button onClick={send}>Execute</button>
    </div>
  );
}

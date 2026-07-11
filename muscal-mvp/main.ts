import { Graph } from "./core/graph";
import { ExecutionEngine } from "./engine/executionEngine";
import { validateGraph } from "./ve/validator";

const graph = new Graph();

graph.addNode({
  id: "start",
  type: "entry",
  run: (input: number) => {
    console.log("Start:", input);
    return input + 1;
  }
});

graph.addNode({
  id: "step1",
  type: "function",
  run: (input: number) => {
    console.log("Step1:", input);
    return input * 2;
  }
});

graph.addEdge({ from: "start", to: "step1" });

const validation = validateGraph(graph);

if (!validation.valid) {
  throw new Error("Graph invalid: " + JSON.stringify(validation));
}

const engine = new ExecutionEngine(graph);

engine.run("start", 1).then(console.log);

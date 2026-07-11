import { Graph } from "../core/graph";

export function validateGraph(graph: Graph) {
  const orphanNodes = [];

  for (const node of graph.nodes.values()) {
    const hasIncoming = graph.edges.some(e => e.to === node.id);
    const isEntry = node.type === "entry";

    if (!hasIncoming && !isEntry) {
      orphanNodes.push(node.id);
    }
  }

  const hasEntry = [...graph.nodes.values()]
    .some(n => n.type === "entry");

  return {
    valid: orphanNodes.length === 0 && hasEntry,
    orphanNodes,
    hasEntry
  };
}

import { Node } from "./node";
import { Edge } from "./edge";

export class Graph {
  nodes = new Map<string, Node>();
  edges: Edge[] = [];

  addNode(node: Node) {
    this.nodes.set(node.id, node);
  }

  addEdge(edge: Edge) {
    this.edges.push(edge);
  }

  getNext(nodeId: string) {
    return this.edges
      .filter(e => e.from === nodeId)
      .map(e => this.nodes.get(e.to))
      .filter(Boolean);
  }
}

import { Graph } from "../core/graph";

export class ExecutionEngine {
  constructor(private graph: Graph) {}

  async run(startId: string, input: any): Promise<any> {
    const node = this.graph.nodes.get(startId);
    if (!node) throw new Error("Start node not found");

    const output = await node.run(input);

    const nextNodes = this.graph.getNext(node.id);

    for (const next of nextNodes) {
      if (next) {
        await this.run(next.id, output);
      }
    }

    return output;
  }
}

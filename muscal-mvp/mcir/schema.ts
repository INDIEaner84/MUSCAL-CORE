export interface MCIRGraph {
  nodes: {
    id: string;
    type: string;
  }[];
  edges: {
    from: string;
    to: string;
  }[];
}

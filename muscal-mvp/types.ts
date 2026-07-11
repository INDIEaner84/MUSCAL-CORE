export interface Node {
  id: string;
  type: "entry" | "function" | "end";
  run: (input: any) => any;
}

export interface Edge {
  from: string;
  to: string;
}

export type FlowNode = {
  id: string;
  /** The question this node asks the model. Must be answerable YES or NO. */
  prompt: string;
  /** Terminal nodes stop the run and report their label as the outcome. */
  terminal?: boolean;
  label?: string;
  position: { x: number; y: number };
};

export type FlowEdge = {
  id: string;
  source: string;
  target: string;
  /** Which answer sends the run down this edge. */
  branch: "YES" | "NO";
};

export type Graph = { nodes: FlowNode[]; edges: FlowEdge[] };

export type StepResult = {
  nodeId: string;
  prompt: string;
  answer: "YES" | "NO" | null;
  raw: string;
  error?: string;
};

export type Run = {
  id: string;
  input: string;
  status: "running" | "done" | "failed";
  steps: StepResult[];
  outcome?: string;
  error?: string;
};

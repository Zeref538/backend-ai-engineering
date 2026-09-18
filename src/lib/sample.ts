import type { Graph } from "./types";

/** A support triage flow: two questions, three outcomes. */
export const sampleGraph: Graph = {
  nodes: [
    { id: "n1", prompt: "Is this a support request?", position: { x: 40, y: 140 } },
    { id: "n2", prompt: "Is the customer asking for a refund?", position: { x: 360, y: 40 } },
    { id: "sales", prompt: "", terminal: true, label: "Send to Sales", position: { x: 380, y: 300 } },
    { id: "refunds", prompt: "", terminal: true, label: "Send to Refunds", position: { x: 700, y: 0 } },
    { id: "support", prompt: "", terminal: true, label: "Send to Support", position: { x: 700, y: 160 } },
  ],
  edges: [
    { id: "e1", source: "n1", target: "n2", branch: "YES" },
    { id: "e2", source: "n1", target: "sales", branch: "NO" },
    { id: "e3", source: "n2", target: "refunds", branch: "YES" },
    { id: "e4", source: "n2", target: "support", branch: "NO" },
  ],
};

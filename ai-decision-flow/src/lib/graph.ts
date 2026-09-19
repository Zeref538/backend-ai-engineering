import type { FlowNode, Graph } from "./types";

/**
 * Walking the graph, kept away from the AI and from Inngest.
 *
 * These are plain functions over plain data, which is the whole reason they can
 * be tested in milliseconds with no server, no key and no network.
 */

/** The start is the node nothing points at. */
export function startNode(graph: Graph): FlowNode | null {
  const targets = new Set(graph.edges.map((e) => e.target));
  const starts = graph.nodes.filter((n) => !targets.has(n.id));
  return starts.length === 1 ? starts[0] : (starts[0] ?? null);
}

/** Where an answer takes you, or a plain-English reason it takes you nowhere. */
export function nextNode(
  graph: Graph,
  fromId: string,
  answer: "YES" | "NO",
): { node?: FlowNode; error?: string } {
  const edge = graph.edges.find((e) => e.source === fromId && e.branch === answer);
  if (!edge) return { error: `Node "${fromId}" answered ${answer} but has no ${answer} edge.` };
  const node = graph.nodes.find((n) => n.id === edge.target);
  if (!node) return { error: `Edge points at a node that does not exist: ${edge.target}` };
  return { node };
}

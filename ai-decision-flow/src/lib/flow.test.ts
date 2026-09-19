/**
 * Run: npm test
 *
 * Node 24 strips the TypeScript types and runs the file directly, so there is
 * no build step and no test framework to install.
 */
import assert from "node:assert/strict";
import test from "node:test";

import { nextNode, startNode } from "./graph.ts";
import { normalize } from "./decide.ts";
import { sampleGraph } from "./sample.ts";

test("a chatty model still gives a usable answer", () => {
  // Every one of these is something a model really replies with.
  assert.equal(normalize("YES"), "YES");
  assert.equal(normalize("Yes."), "YES");
  assert.equal(normalize("  no  "), "NO");
  assert.equal(normalize("**YES**"), "YES");
  assert.equal(normalize("yes, this is a support request"), "YES");
  assert.equal(normalize("NO - the customer is asking about pricing"), "NO");
});

test("an answer that is neither is rejected, not guessed", () => {
  // Guessing here would send the run down the wrong branch and never say so.
  assert.equal(normalize("maybe"), null);
  assert.equal(normalize(""), null);
  assert.equal(normalize("I cannot determine that"), null);
  assert.equal(normalize("42"), null);
});

test("the start node is the one nothing points at", () => {
  assert.equal(startNode(sampleGraph)?.id, "n1");
});

test("YES and NO lead to different places", () => {
  assert.equal(nextNode(sampleGraph, "n1", "YES").node?.id, "n2");
  assert.equal(nextNode(sampleGraph, "n1", "NO").node?.id, "sales");
  assert.equal(nextNode(sampleGraph, "n2", "YES").node?.id, "refunds");
  assert.equal(nextNode(sampleGraph, "n2", "NO").node?.id, "support");
});

test("a missing branch is an error with a readable reason", () => {
  const broken = {
    nodes: [{ id: "a", prompt: "Is it?", position: { x: 0, y: 0 } }],
    edges: [],
  };
  const hop = nextNode(broken, "a", "YES");
  assert.equal(hop.node, undefined);
  assert.match(hop.error ?? "", /has no YES edge/);
});

test("an edge pointing at nothing is caught", () => {
  const broken = {
    nodes: [{ id: "a", prompt: "Is it?", position: { x: 0, y: 0 } }],
    edges: [{ id: "e", source: "a", target: "ghost", branch: "YES" as const }],
  };
  assert.match(nextNode(broken, "a", "YES").error ?? "", /does not exist/);
});

test("every terminal node in the sample flow is reachable", () => {
  const reachable = new Set(sampleGraph.edges.map((e) => e.target));
  for (const n of sampleGraph.nodes.filter((n) => n.terminal)) {
    assert.ok(reachable.has(n.id), `${n.id} is unreachable`);
  }
});

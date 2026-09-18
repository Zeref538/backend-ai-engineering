import { decide } from "@/lib/decide";
import { getRun, putRun } from "@/lib/runs";
import { nextNode, startNode } from "@/lib/graph";
import type { FlowNode, Graph, Run, StepResult } from "@/lib/types";
import { inngest } from "./client";

/** Hard stop, so a flow wired into a loop can't run forever. */
const MAX_STEPS = 20;

export const runFlow = inngest.createFunction(
  // Inngest v4 takes two arguments: options (with the trigger inside) and the
  // handler. v3 took the trigger as a separate second argument.
  { id: "run-flow", retries: 1, triggers: [{ event: "flow/run" }] },
  async ({ event, step }) => {
    const { runId, graph, input } = event.data as {
      runId: string;
      graph: Graph;
      input: string;
    };

    const run: Run = { id: runId, input, status: "running", steps: [] };
    putRun(run);

    let current = startNode(graph);
    if (!current) {
      putRun({ ...run, status: "failed", error: "No start node: every node has an incoming edge." });
      return { status: "failed" };
    }

    const steps: StepResult[] = [];

    for (let i = 0; i < MAX_STEPS; i++) {
      if (current.terminal) {
        putRun({ ...run, status: "done", steps, outcome: current.label || current.id });
        return { status: "done", outcome: current.label || current.id };
      }

      const node: FlowNode = current;
      // One node, one Inngest step. Each step's result is saved once it
      // succeeds, so a retry resumes here instead of re-asking every earlier
      // question -- which would also mean paying for them twice.
      let result: StepResult;
      try {
        result = await step.run(`decide-${node.id}`, async () => {
          const { answer, raw } = await decide(node.prompt, input);
          return { nodeId: node.id, prompt: node.prompt, answer, raw } as StepResult;
        });
      } catch (err) {
        const message = err instanceof Error ? err.message : String(err);
        steps.push({ nodeId: node.id, prompt: node.prompt, answer: null, raw: "", error: message });
        putRun({ ...run, status: "failed", steps, error: message });
        throw err; // let Inngest record the failure and retry
      }

      steps.push(result);
      putRun({ ...getRun(runId)!, steps });

      const hop = nextNode(graph, node.id, result.answer!);
      if (hop.error || !hop.node) {
        const message = hop.error ?? "Nowhere to go from here.";
        putRun({ ...run, status: "failed", steps, error: message });
        return { status: "failed", error: message };
      }
      current = hop.node;
    }

    const message = `Stopped after ${MAX_STEPS} steps -- the flow probably loops.`;
    putRun({ ...run, status: "failed", steps, error: message });
    return { status: "failed", error: message };
  },
);

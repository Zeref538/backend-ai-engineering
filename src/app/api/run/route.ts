import { NextResponse } from "next/server";

import { inngest } from "@/inngest/client";
import { listRuns, putRun } from "@/lib/runs";
import type { Graph } from "@/lib/types";

export async function POST(request: Request) {
  const body = await request.json().catch(() => null);
  if (!body || typeof body.input !== "string" || !body.input.trim()) {
    return NextResponse.json({ error: "Field 'input' is required" }, { status: 400 });
  }
  const graph = body.graph as Graph;
  if (!graph?.nodes?.length) {
    return NextResponse.json({ error: "The flow has no nodes" }, { status: 400 });
  }

  const runId = `run_${Date.now().toString(36)}`;
  putRun({ id: runId, input: body.input, status: "running", steps: [] });
  await inngest.send({ name: "flow/run", data: { runId, graph, input: body.input } });

  // 202: taken, not finished. The client polls /api/run/<id> from here.
  return NextResponse.json({ runId, status: "running" }, { status: 202 });
}

export async function GET() {
  return NextResponse.json(listRuns());
}

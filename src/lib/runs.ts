import type { Run } from "./types";

/**
 * Where runs live while they happen.
 *
 * A module-level Map is wiped on every restart and would not survive more than
 * one server instance. That is the right amount of storage for this assignment
 * and the wrong amount for anything real -- a database is the upgrade.
 */
const store = new Map<string, Run>();

export const putRun = (run: Run) => store.set(run.id, run);
export const getRun = (id: string) => store.get(id);
export const listRuns = () => [...store.values()].reverse();

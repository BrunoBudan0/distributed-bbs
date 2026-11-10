import { setTimeout as waitForTimer } from "node:timers/promises";

export async function waitMilliseconds(durationMs: number): Promise<void> {
  await waitForTimer(durationMs);
}

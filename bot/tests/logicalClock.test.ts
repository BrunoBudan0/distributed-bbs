import assert from "node:assert/strict";
import { test } from "node:test";

import { MAX_LOGICAL_CLOCK } from "../src/constants.js";
import { LogicalClock } from "../src/models/logicalClock.js";

test("the logical clock starts at zero and increments before each send", () => {
  const logicalClock = new LogicalClock();

  const sentValues = [logicalClock.tickForSend(), logicalClock.tickForSend(), logicalClock.tickForSend()];

  assert.deepEqual(sentValues, [1, 2, 3]);
});

test("observing a larger logical clock adopts it and the next send goes beyond it", () => {
  const logicalClock = new LogicalClock();

  logicalClock.observe(10);

  assert.equal(logicalClock.tickForSend(), 11);
});

test("observing a smaller logical clock keeps the current value", () => {
  const logicalClock = new LogicalClock();
  logicalClock.tickForSend();
  logicalClock.tickForSend();
  logicalClock.tickForSend();

  logicalClock.observe(1);

  assert.equal(logicalClock.tickForSend(), 4);
});

test("after observing the maximum the logical clock stays at the maximum instead of going beyond it", () => {
  const logicalClock = new LogicalClock();

  logicalClock.observe(MAX_LOGICAL_CLOCK);

  assert.equal(logicalClock.tickForSend(), MAX_LOGICAL_CLOCK);
});

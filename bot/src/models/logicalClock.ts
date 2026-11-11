import { MAX_LOGICAL_CLOCK } from "../constants.js";

export class LogicalClock {
  private counter = 0;

  tickForSend(): number {
    this.counter = Math.min(this.counter + 1, MAX_LOGICAL_CLOCK);
    return this.counter;
  }

  observe(receivedCounter: number): void {
    this.counter = Math.max(this.counter, receivedCounter);
  }
}

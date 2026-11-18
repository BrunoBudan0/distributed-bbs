import assert from "node:assert/strict";
import { test } from "node:test";

import { Operation, ResponseMessage, ResponseStatus } from "../src/dtos/messages.js";
import { UnexpectedResponse } from "../src/errors/customErrors.js";
import { historyPublicationsFrom } from "../src/schemas/responseSchema.js";

const VALID_HISTORY_PUBLICATION = {
  author: "bot-2",
  message: "Bom dia, pessoal!",
  timestamp: 1_763_000_000_000,
  server: "server-2",
};

const HISTORIES_OUTSIDE_THE_PROTOCOL: [description: string, publications: unknown][] = [
  ["no list of publications", undefined],
  ["a map in place of the list", { first: VALID_HISTORY_PUBLICATION }],
  ["an entry that is not a map", ["Bom dia, pessoal!"]],
  ["an entry without the author", [{ ...VALID_HISTORY_PUBLICATION, author: undefined }]],
  ["a message that is a number", [{ ...VALID_HISTORY_PUBLICATION, message: 7 }]],
  ["a timestamp written as text", [{ ...VALID_HISTORY_PUBLICATION, timestamp: "1763000000000" }]],
  ["a fractional timestamp", [{ ...VALID_HISTORY_PUBLICATION, timestamp: 1.5 }]],
  ["an entry without the server", [{ ...VALID_HISTORY_PUBLICATION, server: undefined }]],
];

function historyResponseWith(publications: unknown): ResponseMessage {
  return {
    operation: Operation.ChannelHistory,
    sender: "server-1",
    timestamp: 1_000,
    logical_clock: 1,
    status: ResponseStatus.Success,
    payload: { channel: "news", publications },
  };
}

test("a history inside the protocol is handed over as it arrived", () => {
  const historyPublications = historyPublicationsFrom(historyResponseWith([VALID_HISTORY_PUBLICATION]));

  assert.deepEqual(historyPublications, [VALID_HISTORY_PUBLICATION]);
});

test("a channel without publications has an empty history", () => {
  assert.deepEqual(historyPublicationsFrom(historyResponseWith([])), []);
});

for (const [description, publications] of HISTORIES_OUTSIDE_THE_PROTOCOL) {
  test(`a history with ${description} is refused as outside the protocol`, () => {
    assert.throws(() => historyPublicationsFrom(historyResponseWith(publications)), UnexpectedResponse);
  });
}

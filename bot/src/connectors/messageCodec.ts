import { decode, encode } from "@msgpack/msgpack";

import { RequestMessage } from "../dtos/messages.js";

export function encodeMessage(request: RequestMessage): Uint8Array {
  return encode(request);
}

export function decodeMessage(encodedMessage: Uint8Array): unknown {
  return decode(encodedMessage);
}

import { inspect } from "node:util";

export class BrokerTimeout extends Error {
  constructor(timeoutMs: number) {
    super(`no response from the broker within ${timeoutMs} ms`);
  }
}

export class UnexpectedResponse extends Error {
  constructor(decodedMessage: unknown) {
    super(`the server answered outside the protocol: ${inspect(decodedMessage, { depth: null })}`);
  }
}

export class MissingEnvironmentVariable extends Error {
  constructor(variableName: string) {
    super(`the environment variable ${variableName} is required`);
  }
}

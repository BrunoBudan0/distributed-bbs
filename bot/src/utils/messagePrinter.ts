import { inspect } from "node:util";

import { TIMESTAMP_FIELD } from "../constants.js";
import { RequestMessage, ResponseMessage } from "../dtos/messages.js";
import { BrokerTimeout } from "../errors/customErrors.js";

const SENT_LABEL = "SENT    ";
const RECEIVED_LABEL = "RECEIVED";
const TIMEOUT_LABEL = "TIMEOUT ";
const FIELD_SEPARATOR = " | ";

export function printSentMessage(request: RequestMessage): void {
  printLine(SENT_LABEL, describedMessage(request));
}

export function printReceivedMessage(response: ResponseMessage): void {
  printLine(RECEIVED_LABEL, describedMessage(response));
}

export function printBrokerTimeout(brokerTimeout: BrokerTimeout): void {
  printLine(TIMEOUT_LABEL, brokerTimeout.message);
}

function printLine(directionLabel: string, description: string): void {
  console.log(`${directionLabel}${FIELD_SEPARATOR}${description}`);
}

function describedMessage(message: RequestMessage | ResponseMessage): string {
  return Object.entries(message)
    .map(([fieldName, fieldValue]) => `${fieldName}=${describedField(fieldName, fieldValue)}`)
    .join(FIELD_SEPARATOR);
}

function describedField(fieldName: string, fieldValue: unknown): string {
  if (fieldName === TIMESTAMP_FIELD) {
    return new Date(fieldValue as number).toISOString();
  }

  return inspect(fieldValue, { depth: null, breakLength: Infinity });
}

import { inspect } from "node:util";

import { TIMESTAMP_FIELD } from "../constants.js";
import { PublicationMessage, RequestMessage, ResponseMessage } from "../dtos/messages.js";
import { BrokerTimeout } from "../errors/customErrors.js";

const SENT_LABEL = "SENT";
const RECEIVED_LABEL = "RECEIVED";
const TIMEOUT_LABEL = "TIMEOUT";
const SUBSCRIBED_LABEL = "SUBSCRIBED";
const LABEL_WIDTH = SUBSCRIBED_LABEL.length;
const FIELD_SEPARATOR = " | ";

type PrintableMessage = RequestMessage | ResponseMessage | PublicationMessage;

export function printSentMessage(request: RequestMessage): void {
  printLine(SENT_LABEL, describedMessage(request));
}

export function printReceivedMessage(response: ResponseMessage): void {
  printLine(RECEIVED_LABEL, describedMessage(response));
}

export function printReceivedPublication(topic: string, publication: PublicationMessage, receivedAtMs: number): void {
  printLine(
    RECEIVED_LABEL,
    [`topic=${inspect(topic)}`, describedMessage(publication), `received_at=${readableTimestamp(receivedAtMs)}`].join(
      FIELD_SEPARATOR,
    ),
  );
}

export function printSubscription(channelName: string): void {
  printLine(SUBSCRIBED_LABEL, `channel=${inspect(channelName)}`);
}

export function printBrokerTimeout(brokerTimeout: BrokerTimeout): void {
  printLine(TIMEOUT_LABEL, brokerTimeout.message);
}

function printLine(label: string, description: string): void {
  console.log(`${label.padEnd(LABEL_WIDTH)}${FIELD_SEPARATOR}${description}`);
}

function describedMessage(message: PrintableMessage): string {
  return Object.entries(message)
    .map(([fieldName, fieldValue]) => `${fieldName}=${describedField(fieldName, fieldValue)}`)
    .join(FIELD_SEPARATOR);
}

function describedField(fieldName: string, fieldValue: unknown): string {
  if (fieldName === TIMESTAMP_FIELD) {
    return readableTimestamp(fieldValue as number);
  }

  return inspect(fieldValue, { depth: null, breakLength: Infinity });
}

function readableTimestamp(timestampMs: number): string {
  return new Date(timestampMs).toISOString();
}

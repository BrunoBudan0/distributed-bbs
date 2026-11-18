import { CHANNELS_FIELD, PUBLICATIONS_FIELD } from "../constants.js";
import { HistoryPublication, ResponseMessage, ResponseStatus } from "../dtos/messages.js";
import { UnexpectedResponse } from "../errors/customErrors.js";
import { isListOfTexts, isMap } from "./valueChecks.js";

const KNOWN_RESPONSE_STATUSES: unknown[] = Object.values(ResponseStatus);

export function responseFrom(decodedMessage: unknown): ResponseMessage {
  if (!isResponseMessage(decodedMessage)) {
    throw new UnexpectedResponse(decodedMessage);
  }

  return decodedMessage;
}

export function channelNamesFrom(response: ResponseMessage): string[] {
  const channelNames = response.payload[CHANNELS_FIELD];
  if (!isListOfTexts(channelNames)) {
    throw new UnexpectedResponse(response);
  }

  return channelNames;
}

export function historyPublicationsFrom(response: ResponseMessage): HistoryPublication[] {
  const historyPublications = response.payload[PUBLICATIONS_FIELD];
  if (!isListOfHistoryPublications(historyPublications)) {
    throw new UnexpectedResponse(response);
  }

  return historyPublications;
}

function isResponseMessage(decodedMessage: unknown): decodedMessage is ResponseMessage {
  if (!isMap(decodedMessage)) {
    return false;
  }

  return (
    typeof decodedMessage.operation === "string" &&
    typeof decodedMessage.sender === "string" &&
    Number.isInteger(decodedMessage.timestamp) &&
    Number.isSafeInteger(decodedMessage.logical_clock) &&
    KNOWN_RESPONSE_STATUSES.includes(decodedMessage.status) &&
    isMap(decodedMessage.payload)
  );
}

function isListOfHistoryPublications(decodedValue: unknown): decodedValue is HistoryPublication[] {
  return Array.isArray(decodedValue) && decodedValue.every(isHistoryPublication);
}

function isHistoryPublication(decodedValue: unknown): decodedValue is HistoryPublication {
  if (!isMap(decodedValue)) {
    return false;
  }

  return (
    typeof decodedValue.author === "string" &&
    typeof decodedValue.message === "string" &&
    Number.isInteger(decodedValue.timestamp) &&
    typeof decodedValue.server === "string"
  );
}

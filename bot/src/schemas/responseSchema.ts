import { CHANNELS_FIELD } from "../constants.js";
import { ResponseMessage, ResponseStatus } from "../dtos/messages.js";
import { UnexpectedResponse } from "../errors/customErrors.js";

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

function isResponseMessage(decodedMessage: unknown): decodedMessage is ResponseMessage {
  if (!isMap(decodedMessage)) {
    return false;
  }

  return (
    typeof decodedMessage.operation === "string" &&
    typeof decodedMessage.sender === "string" &&
    Number.isInteger(decodedMessage.timestamp) &&
    KNOWN_RESPONSE_STATUSES.includes(decodedMessage.status) &&
    isMap(decodedMessage.payload)
  );
}

function isMap(decodedValue: unknown): decodedValue is Record<string, unknown> {
  return typeof decodedValue === "object" && decodedValue !== null && !Array.isArray(decodedValue);
}

function isListOfTexts(decodedValue: unknown): decodedValue is string[] {
  return Array.isArray(decodedValue) && decodedValue.every((item) => typeof item === "string");
}

import { PublicationMessage } from "../dtos/messages.js";
import { UnexpectedPublication } from "../errors/customErrors.js";
import { isMap } from "./valueChecks.js";

export function publicationFrom(decodedMessage: unknown): PublicationMessage {
  if (!isPublicationMessage(decodedMessage)) {
    throw new UnexpectedPublication(decodedMessage);
  }

  return decodedMessage;
}

function isPublicationMessage(decodedMessage: unknown): decodedMessage is PublicationMessage {
  if (!isMap(decodedMessage) || !isMap(decodedMessage.payload)) {
    return false;
  }

  return (
    typeof decodedMessage.operation === "string" &&
    typeof decodedMessage.sender === "string" &&
    Number.isInteger(decodedMessage.timestamp) &&
    Number.isSafeInteger(decodedMessage.logical_clock) &&
    typeof decodedMessage.payload.channel === "string" &&
    typeof decodedMessage.payload.author === "string" &&
    typeof decodedMessage.payload.message === "string"
  );
}

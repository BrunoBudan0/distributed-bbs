import { CHANNEL_FIELD, MESSAGE_FIELD } from "../constants.js";
import { Operation, RequestMessage, ResponseMessage } from "../dtos/messages.js";
import { LogicalClock } from "../models/logicalClock.js";
import { responseFrom } from "../schemas/responseSchema.js";
import { currentTimestampMs } from "../utils/clock.js";
import { printReceivedMessage, printSentMessage } from "../utils/messagePrinter.js";
import { BrokerSocket } from "./brokerSocket.js";
import { decodeMessage, encodeMessage } from "./messageCodec.js";

export class BbsConnector {
  constructor(
    private readonly username: string,
    private readonly brokerSocket: BrokerSocket,
    private readonly logicalClock: LogicalClock,
  ) {}

  logIn(): Promise<ResponseMessage> {
    return this.exchange(Operation.Login, {});
  }

  createChannel(channelName: string): Promise<ResponseMessage> {
    return this.exchange(Operation.CreateChannel, { [CHANNEL_FIELD]: channelName });
  }

  listChannels(): Promise<ResponseMessage> {
    return this.exchange(Operation.ListChannels, {});
  }

  publish(channelName: string, message: string): Promise<ResponseMessage> {
    return this.exchange(Operation.Publish, { [CHANNEL_FIELD]: channelName, [MESSAGE_FIELD]: message });
  }

  private async exchange(operation: Operation, payload: Record<string, string>): Promise<ResponseMessage> {
    const request: RequestMessage = {
      operation,
      sender: this.username,
      timestamp: currentTimestampMs(),
      logical_clock: this.logicalClock.tickForSend(),
      payload,
    };
    printSentMessage(request);

    const encodedResponse = await this.brokerSocket.exchange(encodeMessage(request));
    const response = responseFrom(decodeMessage(encodedResponse));
    printReceivedMessage(response);
    this.logicalClock.observe(response.logical_clock);
    return response;
  }
}

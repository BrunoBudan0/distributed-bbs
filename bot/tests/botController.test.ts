import assert from "node:assert/strict";
import { test } from "node:test";

import { BbsConnector } from "../src/connectors/bbsConnector.js";
import { ChannelSubscriber } from "../src/connectors/channelSubscriber.js";
import { CHANNEL_CATALOG } from "../src/constants.js";
import { BotController } from "../src/controllers/botController.js";
import { Operation, ResponseMessage, ResponseStatus } from "../src/dtos/messages.js";

const SUBSCRIBE_ACTION = "subscribe";

type RecordedCall = [action: string, channelName?: string];

class FirstRoundFinished extends Error {}

function responseWith(status: ResponseStatus, payload: Record<string, unknown>): ResponseMessage {
  return { operation: "any", sender: "server-1", timestamp: 1_000, logical_clock: 1, status, payload };
}

class RecordingBbsConnector {
  readonly recordedCalls: RecordedCall[] = [];

  constructor(private readonly historyResponse: ResponseMessage) {}

  async logIn(): Promise<ResponseMessage> {
    this.recordedCalls.push([Operation.Login]);
    return responseWith(ResponseStatus.Success, {});
  }

  async listChannels(): Promise<ResponseMessage> {
    this.recordedCalls.push([Operation.ListChannels]);
    return responseWith(ResponseStatus.Success, { channels: CHANNEL_CATALOG });
  }

  async createChannel(channelName: string): Promise<ResponseMessage> {
    this.recordedCalls.push([Operation.CreateChannel, channelName]);
    return responseWith(ResponseStatus.Success, {});
  }

  async channelHistory(channelName: string): Promise<ResponseMessage> {
    this.recordedCalls.push([Operation.ChannelHistory, channelName]);
    return this.historyResponse;
  }

  async publish(channelName: string): Promise<never> {
    this.recordedCalls.push([Operation.Publish, channelName]);
    throw new FirstRoundFinished();
  }
}

class RecordingChannelSubscriber {
  private readonly subscribedChannelNames: string[] = [];

  constructor(private readonly recordedCalls: RecordedCall[]) {}

  subscribedChannels(): string[] {
    return [...this.subscribedChannelNames];
  }

  subscribe(channelName: string): void {
    this.subscribedChannelNames.push(channelName);
    this.recordedCalls.push([SUBSCRIBE_ACTION, channelName]);
  }

  receivePublicationsForever(): Promise<never> {
    return new Promise<never>(() => undefined);
  }
}

async function callsOfTheFirstRound(historyResponse: ResponseMessage): Promise<RecordedCall[]> {
  const bbsConnector = new RecordingBbsConnector(historyResponse);
  const channelSubscriber = new RecordingChannelSubscriber(bbsConnector.recordedCalls);
  const botController = new BotController(
    bbsConnector as unknown as BbsConnector,
    channelSubscriber as unknown as ChannelSubscriber,
  );

  await assert.rejects(botController.run(), FirstRoundFinished);
  return bbsConnector.recordedCalls;
}

test("right after subscribing the bot asks for the history of the subscribed channel and then publishes", async () => {
  const recordedCalls = await callsOfTheFirstRound(
    responseWith(ResponseStatus.Success, {
      channel: "news",
      publications: [{ author: "bot-2", message: "Bom dia, pessoal!", timestamp: 1_000, server: "server-2" }],
    }),
  );

  const [subscription, historyRequest, publication] = recordedCalls.slice(2);
  assert.deepEqual(recordedCalls.slice(0, 2), [[Operation.Login], [Operation.ListChannels]]);
  assert.equal(subscription[0], SUBSCRIBE_ACTION);
  assert.deepEqual(historyRequest, [Operation.ChannelHistory, subscription[1]]);
  assert.equal(publication[0], Operation.Publish);
  assert.equal(recordedCalls.length, 5);
});

test("a refused history request does not stop the bot from publishing", async () => {
  const recordedCalls = await callsOfTheFirstRound(
    responseWith(ResponseStatus.Error, {
      error_code: "CHANNEL_NOT_FOUND",
      error_description: "there is no channel with this name on this server",
    }),
  );

  assert.equal(recordedCalls.at(-1)?.[0], Operation.Publish);
});

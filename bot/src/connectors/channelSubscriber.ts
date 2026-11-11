import { Context, Subscriber } from "zeromq";

import { SubscriptionClosed } from "../errors/customErrors.js";
import { publicationFrom } from "../schemas/publicationSchema.js";
import { currentTimestampMs } from "../utils/clock.js";
import { printReceivedPublication, printSubscription } from "../utils/messagePrinter.js";
import { decodeMessage } from "./messageCodec.js";

export class ChannelSubscriber {
  private readonly subscriberSocket = new Subscriber({ context: new Context() });
  private readonly subscribedChannelNames = new Set<string>();

  constructor(proxyEndpoint: string) {
    this.subscriberSocket.connect(proxyEndpoint);
  }

  subscribedChannels(): string[] {
    return [...this.subscribedChannelNames];
  }

  subscribe(channelName: string): void {
    this.subscriberSocket.subscribe(channelName);
    this.subscribedChannelNames.add(channelName);
    printSubscription(channelName);
  }

  async receivePublicationsForever(): Promise<never> {
    for await (const [encodedTopic, encodedPublication] of this.subscriberSocket) {
      const receivedAtMs = currentTimestampMs();
      const topic = encodedTopic.toString();
      if (this.subscribedChannelNames.has(topic)) {
        printReceivedPublication(topic, publicationFrom(decodeMessage(encodedPublication)), receivedAtMs);
      }
    }

    throw new SubscriptionClosed();
  }
}

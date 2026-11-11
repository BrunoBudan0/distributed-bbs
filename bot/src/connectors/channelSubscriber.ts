import { Context, Subscriber } from "zeromq";

import { SubscriptionClosed } from "../errors/customErrors.js";
import { LogicalClock } from "../models/logicalClock.js";
import { publicationFrom } from "../schemas/publicationSchema.js";
import { currentTimestampMs } from "../utils/clock.js";
import { printReceivedPublication, printSubscription } from "../utils/messagePrinter.js";
import { decodeMessage } from "./messageCodec.js";

export class ChannelSubscriber {
  private readonly subscriberSocket = new Subscriber({ context: new Context() });
  private readonly subscribedChannelNames = new Set<string>();

  constructor(
    proxyEndpoint: string,
    private readonly logicalClock: LogicalClock,
  ) {
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
        this.showPublication(topic, encodedPublication, receivedAtMs);
      }
    }

    throw new SubscriptionClosed();
  }

  private showPublication(topic: string, encodedPublication: Uint8Array, receivedAtMs: number): void {
    const publication = publicationFrom(decodeMessage(encodedPublication));
    printReceivedPublication(topic, publication, receivedAtMs);
    this.logicalClock.observe(publication.logical_clock);
  }
}

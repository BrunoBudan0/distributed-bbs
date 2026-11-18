import { BbsConnector } from "../connectors/bbsConnector.js";
import { ChannelSubscriber } from "../connectors/channelSubscriber.js";
import {
  CHANNEL_CATALOG,
  LOGIN_RETRY_INTERVAL_MS,
  MESSAGE_CATALOG,
  MESSAGES_PER_BATCH,
  MINIMUM_CHANNEL_COUNT,
  MINIMUM_SUBSCRIPTION_COUNT,
  PUBLICATION_INTERVAL_MS,
} from "../constants.js";
import { ResponseStatus } from "../dtos/messages.js";
import { BrokerTimeout } from "../errors/customErrors.js";
import { channelNamesFrom, historyPublicationsFrom } from "../schemas/responseSchema.js";
import { currentTimestampMs } from "../utils/clock.js";
import { printBrokerTimeout, printChannelHistory } from "../utils/messagePrinter.js";
import { pickRandomItem } from "../utils/random.js";
import { waitMilliseconds } from "../utils/waiting.js";
import { channelToCreate, channelToPublishIn, channelToSubscribe } from "./botDecisions.js";

export class BotController {
  constructor(
    private readonly bbsConnector: BbsConnector,
    private readonly channelSubscriber: ChannelSubscriber,
  ) {}

  async run(): Promise<never> {
    await this.logInUntilAccepted();

    return Promise.race([this.channelSubscriber.receivePublicationsForever(), this.runRoundsForever()]);
  }

  private async logInUntilAccepted(): Promise<void> {
    while (!(await this.loginWasAccepted())) {
      await waitMilliseconds(LOGIN_RETRY_INTERVAL_MS);
    }
  }

  private async loginWasAccepted(): Promise<boolean> {
    try {
      const loginResponse = await this.bbsConnector.logIn();
      return loginResponse.status === ResponseStatus.Success;
    } catch (loginError) {
      this.printBrokerTimeoutOrRethrow(loginError);
      return false;
    }
  }

  private async runRoundsForever(): Promise<never> {
    while (true) {
      await this.runRoundOrReportTimeout();
    }
  }

  private async runRoundOrReportTimeout(): Promise<void> {
    try {
      await this.runRound();
    } catch (roundError) {
      this.printBrokerTimeoutOrRethrow(roundError);
    }
  }

  private async runRound(): Promise<void> {
    const listedChannelNames = channelNamesFrom(await this.bbsConnector.listChannels());
    await this.createChannelIfBelowMinimum(listedChannelNames);
    await this.subscribeIfBelowMinimum(listedChannelNames);
    await this.publishBatch(channelToPublishIn(listedChannelNames, pickRandomItem));
  }

  private async createChannelIfBelowMinimum(listedChannelNames: string[]): Promise<void> {
    const channelName = channelToCreate(listedChannelNames, CHANNEL_CATALOG, MINIMUM_CHANNEL_COUNT, pickRandomItem);
    if (channelName !== undefined) {
      await this.bbsConnector.createChannel(channelName);
    }
  }

  private async subscribeIfBelowMinimum(listedChannelNames: string[]): Promise<void> {
    const channelName = channelToSubscribe(
      listedChannelNames,
      this.channelSubscriber.subscribedChannels(),
      MINIMUM_SUBSCRIPTION_COUNT,
      pickRandomItem,
    );
    if (channelName !== undefined) {
      this.channelSubscriber.subscribe(channelName);
      await this.showChannelHistory(channelName);
    }
  }

  private async showChannelHistory(channelName: string): Promise<void> {
    const historyResponse = await this.bbsConnector.channelHistory(channelName);
    if (historyResponse.status === ResponseStatus.Success) {
      printChannelHistory(channelName, historyPublicationsFrom(historyResponse), currentTimestampMs());
    }
  }

  private async publishBatch(channelName: string | undefined): Promise<void> {
    if (channelName === undefined) {
      await waitMilliseconds(PUBLICATION_INTERVAL_MS);
      return;
    }

    for (let publishedCount = 0; publishedCount < MESSAGES_PER_BATCH; publishedCount++) {
      await this.bbsConnector.publish(channelName, pickRandomItem(MESSAGE_CATALOG));
      await waitMilliseconds(PUBLICATION_INTERVAL_MS);
    }
  }

  private printBrokerTimeoutOrRethrow(caughtError: unknown): void {
    if (!(caughtError instanceof BrokerTimeout)) {
      throw caughtError;
    }

    printBrokerTimeout(caughtError);
  }
}

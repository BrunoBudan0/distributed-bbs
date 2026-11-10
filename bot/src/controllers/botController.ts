import { BbsConnector } from "../connectors/bbsConnector.js";
import { CHANNEL_CATALOG, CHANNEL_CYCLE_INTERVAL_MS, LOGIN_RETRY_INTERVAL_MS } from "../constants.js";
import { ResponseStatus } from "../dtos/messages.js";
import { BrokerTimeout } from "../errors/customErrors.js";
import { channelNamesFrom } from "../schemas/responseSchema.js";
import { printBrokerTimeout } from "../utils/messagePrinter.js";
import { waitMilliseconds } from "../utils/waiting.js";
import { firstMissingChannel } from "./channelSelection.js";

export class BotController {
  constructor(private readonly bbsConnector: BbsConnector) {}

  async run(): Promise<never> {
    await this.logInUntilAccepted();

    while (true) {
      await this.listChannelsAndCreateFirstMissing();
      await waitMilliseconds(CHANNEL_CYCLE_INTERVAL_MS);
    }
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

  private async listChannelsAndCreateFirstMissing(): Promise<void> {
    try {
      const listingResponse = await this.bbsConnector.listChannels();
      const missingChannelName = firstMissingChannel(channelNamesFrom(listingResponse), CHANNEL_CATALOG);
      if (missingChannelName !== undefined) {
        await this.bbsConnector.createChannel(missingChannelName);
      }
    } catch (cycleError) {
      this.printBrokerTimeoutOrRethrow(cycleError);
    }
  }

  private printBrokerTimeoutOrRethrow(caughtError: unknown): void {
    if (!(caughtError instanceof BrokerTimeout)) {
      throw caughtError;
    }

    printBrokerTimeout(caughtError);
  }
}

import { Request } from "zeromq";

import { RESPONSE_TIMEOUT_MS } from "../constants.js";
import { BrokerTimeout } from "../errors/customErrors.js";

const ZEROMQ_TIMEOUT_ERROR_CODE = "EAGAIN";

export class BrokerSocket {
  private requestSocket: Request;

  constructor(private readonly brokerEndpoint: string) {
    this.requestSocket = this.newConnectedSocket();
  }

  async exchange(encodedRequest: Uint8Array): Promise<Uint8Array> {
    try {
      await this.requestSocket.send(encodedRequest);
      const [encodedResponse] = await this.requestSocket.receive();
      return encodedResponse;
    } catch (exchangeError) {
      this.refuseAnythingButTimeout(exchangeError);
      this.replaceSocket();
      throw new BrokerTimeout(RESPONSE_TIMEOUT_MS);
    }
  }

  private refuseAnythingButTimeout(exchangeError: unknown): void {
    if ((exchangeError as NodeJS.ErrnoException).code !== ZEROMQ_TIMEOUT_ERROR_CODE) {
      throw exchangeError;
    }
  }

  private replaceSocket(): void {
    this.requestSocket.close();
    this.requestSocket = this.newConnectedSocket();
  }

  private newConnectedSocket(): Request {
    const requestSocket = new Request({
      receiveTimeout: RESPONSE_TIMEOUT_MS,
      sendTimeout: RESPONSE_TIMEOUT_MS,
      linger: 0,
    });
    requestSocket.connect(this.brokerEndpoint);
    return requestSocket;
  }
}

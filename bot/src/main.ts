import { BbsConnector } from "./connectors/bbsConnector.js";
import { BrokerSocket } from "./connectors/brokerSocket.js";
import { ChannelSubscriber } from "./connectors/channelSubscriber.js";
import { BROKER_ENDPOINT_VARIABLE, PROXY_ENDPOINT_VARIABLE, USERNAME_VARIABLE } from "./constants.js";
import { BotController } from "./controllers/botController.js";
import { LogicalClock } from "./models/logicalClock.js";
import { requiredEnvironmentVariable } from "./utils/environment.js";

const logicalClock = new LogicalClock();
const brokerSocket = new BrokerSocket(requiredEnvironmentVariable(BROKER_ENDPOINT_VARIABLE));
const bbsConnector = new BbsConnector(requiredEnvironmentVariable(USERNAME_VARIABLE), brokerSocket, logicalClock);
const channelSubscriber = new ChannelSubscriber(requiredEnvironmentVariable(PROXY_ENDPOINT_VARIABLE), logicalClock);

await new BotController(bbsConnector, channelSubscriber).run();

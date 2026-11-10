import { BbsConnector } from "./connectors/bbsConnector.js";
import { BrokerSocket } from "./connectors/brokerSocket.js";
import { BROKER_ENDPOINT_VARIABLE, USERNAME_VARIABLE } from "./constants.js";
import { BotController } from "./controllers/botController.js";
import { requiredEnvironmentVariable } from "./utils/environment.js";

const brokerSocket = new BrokerSocket(requiredEnvironmentVariable(BROKER_ENDPOINT_VARIABLE));
const bbsConnector = new BbsConnector(requiredEnvironmentVariable(USERNAME_VARIABLE), brokerSocket);

await new BotController(bbsConnector).run();

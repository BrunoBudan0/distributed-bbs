export const RESPONSE_TIMEOUT_MS = 5000;
export const LOGIN_RETRY_INTERVAL_MS = 2000;
export const PUBLICATION_INTERVAL_MS = 1000;

export const MAX_LOGICAL_CLOCK = 2 ** 52;

export const MINIMUM_CHANNEL_COUNT = 5;
export const MINIMUM_SUBSCRIPTION_COUNT = 3;
export const MESSAGES_PER_BATCH = 10;

export const CHANNEL_CATALOG = ["general", "news", "sports", "music", "movies"];

export const MESSAGE_CATALOG = [
  "Bom dia, pessoal!",
  "Alguém viu o jogo ontem?",
  "Qual é a novidade de hoje?",
  "Recomendo muito esse filme.",
  "Essa música é ótima.",
  "Vamos marcar alguma coisa?",
  "Concordo totalmente.",
  "Interessante, conta mais.",
  "Até mais tarde!",
  "Boa noite a todos.",
];

export const CHANNEL_FIELD = "channel";
export const CHANNELS_FIELD = "channels";
export const MESSAGE_FIELD = "message";
export const PUBLICATIONS_FIELD = "publications";
export const TIMESTAMP_FIELD = "timestamp";

export const BROKER_ENDPOINT_VARIABLE = "BROKER_CLIENT_ENDPOINT";
export const PROXY_ENDPOINT_VARIABLE = "PROXY_SUBSCRIBER_ENDPOINT";
export const USERNAME_VARIABLE = "BOT_USERNAME";

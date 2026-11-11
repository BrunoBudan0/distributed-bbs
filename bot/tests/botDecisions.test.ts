import assert from "node:assert/strict";
import { test } from "node:test";

import {
  CHANNEL_CATALOG,
  MESSAGES_PER_BATCH,
  MINIMUM_CHANNEL_COUNT,
  MINIMUM_SUBSCRIPTION_COUNT,
  PUBLICATION_INTERVAL_MS,
} from "../src/constants.js";
import { channelToCreate, channelToPublishIn, channelToSubscribe } from "../src/controllers/botDecisions.js";
import { pickRandomItem } from "../src/utils/random.js";

const RANDOM_PICK_REPETITIONS = 200;

function recordingFirstItemPicker(offeredLists: unknown[][]) {
  return <Item>(items: Item[]): Item => {
    offeredLists.push(items);
    return items[0];
  };
}

test("the bot follows the numbers standardized by the statement", () => {
  assert.equal(MINIMUM_CHANNEL_COUNT, 5);
  assert.equal(MINIMUM_SUBSCRIPTION_COUNT, 3);
  assert.equal(MESSAGES_PER_BATCH, 10);
  assert.equal(PUBLICATION_INTERVAL_MS, 1000);
});

test("with four listed channels the channel to create is drawn among the catalog channels missing from the listing", () => {
  const offeredLists: unknown[][] = [];
  const listedChannelNames = ["general", "sports", "music", "other"];

  const channelName = channelToCreate(
    listedChannelNames,
    CHANNEL_CATALOG,
    MINIMUM_CHANNEL_COUNT,
    recordingFirstItemPicker(offeredLists),
  );

  assert.equal(channelName, "news");
  assert.deepEqual(offeredLists, [["news", "movies"]]);
});

test("with five listed channels no channel is created even when catalog channels are missing", () => {
  const listedChannelNames = ["general", "news", "sports", "other-one", "other-two"];

  assert.equal(channelToCreate(listedChannelNames, CHANNEL_CATALOG, MINIMUM_CHANNEL_COUNT, pickRandomItem), undefined);
});

test("with an empty listing the channel to create is drawn from the whole catalog", () => {
  const offeredLists: unknown[][] = [];

  channelToCreate([], CHANNEL_CATALOG, MINIMUM_CHANNEL_COUNT, recordingFirstItemPicker(offeredLists));

  assert.deepEqual(offeredLists, [CHANNEL_CATALOG]);
});

test("with two subscriptions the bot subscribes to a listed channel it is not subscribed to yet", () => {
  const offeredLists: unknown[][] = [];
  const listedChannelNames = ["general", "news", "sports"];

  const channelName = channelToSubscribe(
    listedChannelNames,
    ["general", "news"],
    MINIMUM_SUBSCRIPTION_COUNT,
    recordingFirstItemPicker(offeredLists),
  );

  assert.equal(channelName, "sports");
  assert.deepEqual(offeredLists, [["sports"]]);
});

test("with three subscriptions the bot subscribes to nothing", () => {
  const channelName = channelToSubscribe(
    ["general", "news", "sports", "music"],
    ["general", "news", "sports"],
    MINIMUM_SUBSCRIPTION_COUNT,
    pickRandomItem,
  );

  assert.equal(channelName, undefined);
});

test("when every listed channel is already subscribed the bot subscribes to nothing", () => {
  assert.equal(channelToSubscribe(["general"], ["general"], MINIMUM_SUBSCRIPTION_COUNT, pickRandomItem), undefined);
});

test("the channel to publish in is drawn from the whole listing", () => {
  const offeredLists: unknown[][] = [];
  const listedChannelNames = ["general", "news", "sports"];

  const channelName = channelToPublishIn(listedChannelNames, recordingFirstItemPicker(offeredLists));

  assert.equal(channelName, "general");
  assert.deepEqual(offeredLists, [listedChannelNames]);
});

test("with an empty listing there is no channel to publish in", () => {
  assert.equal(channelToPublishIn([], pickRandomItem), undefined);
});

test("the random picker only returns items of the given list and reaches all of them", () => {
  const pickedItems = new Set<string>();

  for (let repetition = 0; repetition < RANDOM_PICK_REPETITIONS; repetition++) {
    pickedItems.add(pickRandomItem(CHANNEL_CATALOG));
  }

  assert.deepEqual([...pickedItems].sort(), [...CHANNEL_CATALOG].sort());
});

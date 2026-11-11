export type RandomItemPicker = <Item>(items: Item[]) => Item;

export function channelToCreate(
  listedChannelNames: string[],
  channelCatalog: string[],
  minimumChannelCount: number,
  pickRandomItem: RandomItemPicker,
): string | undefined {
  if (listedChannelNames.length >= minimumChannelCount) {
    return undefined;
  }

  const missingCatalogChannelNames = channelCatalog.filter(
    (channelName) => !listedChannelNames.includes(channelName),
  );
  if (missingCatalogChannelNames.length === 0) {
    return undefined;
  }

  return pickRandomItem(missingCatalogChannelNames);
}

export function channelToSubscribe(
  listedChannelNames: string[],
  subscribedChannelNames: string[],
  minimumSubscriptionCount: number,
  pickRandomItem: RandomItemPicker,
): string | undefined {
  if (subscribedChannelNames.length >= minimumSubscriptionCount) {
    return undefined;
  }

  const unsubscribedChannelNames = listedChannelNames.filter(
    (channelName) => !subscribedChannelNames.includes(channelName),
  );
  if (unsubscribedChannelNames.length === 0) {
    return undefined;
  }

  return pickRandomItem(unsubscribedChannelNames);
}

export function channelToPublishIn(
  listedChannelNames: string[],
  pickRandomItem: RandomItemPicker,
): string | undefined {
  if (listedChannelNames.length === 0) {
    return undefined;
  }

  return pickRandomItem(listedChannelNames);
}

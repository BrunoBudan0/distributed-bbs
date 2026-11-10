export function firstMissingChannel(existingChannelNames: string[], channelCatalog: string[]): string | undefined {
  return channelCatalog.find((channelName) => !existingChannelNames.includes(channelName));
}

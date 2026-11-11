export function pickRandomItem<Item>(items: Item[]): Item {
  return items[Math.floor(Math.random() * items.length)];
}

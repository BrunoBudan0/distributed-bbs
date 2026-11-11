export function isMap(decodedValue: unknown): decodedValue is Record<string, unknown> {
  return typeof decodedValue === "object" && decodedValue !== null && !Array.isArray(decodedValue);
}

export function isListOfTexts(decodedValue: unknown): decodedValue is string[] {
  return Array.isArray(decodedValue) && decodedValue.every((item) => typeof item === "string");
}

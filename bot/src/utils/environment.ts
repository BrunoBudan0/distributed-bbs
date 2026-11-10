import { MissingEnvironmentVariable } from "../errors/customErrors.js";

export function requiredEnvironmentVariable(variableName: string): string {
  const variableValue = process.env[variableName];
  if (variableValue === undefined) {
    throw new MissingEnvironmentVariable(variableName);
  }

  return variableValue;
}

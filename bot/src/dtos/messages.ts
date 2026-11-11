export enum Operation {
  Login = "login",
  CreateChannel = "create_channel",
  ListChannels = "list_channels",
  Publish = "publish",
}

export enum ResponseStatus {
  Success = "success",
  Error = "error",
}

export interface RequestMessage {
  operation: Operation;
  sender: string;
  timestamp: number;
  payload: Record<string, string>;
}

export interface ResponseMessage {
  operation: string;
  sender: string;
  timestamp: number;
  status: ResponseStatus;
  payload: Record<string, unknown>;
}

export interface PublicationMessage {
  operation: string;
  sender: string;
  timestamp: number;
  payload: {
    channel: string;
    author: string;
    message: string;
  };
}

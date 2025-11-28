export type StreamType = "network" | "app" | "visual";

export interface BaseEvent {
  sessionId: string;
  ts: string; // ISO timestamp
  stream: StreamType;
  direction: "client_to_server" | "server_to_client";
}

export interface RawStreamEvent extends BaseEvent {
  type: "raw_chunk";
  length: number;
}

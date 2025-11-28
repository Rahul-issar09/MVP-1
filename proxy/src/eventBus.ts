import { EventEmitter } from "events";
import type { RawStreamEvent } from "./types";

export type ProxyEvent = RawStreamEvent;

class ProxyEventBus extends EventEmitter {
  emitEvent(event: ProxyEvent) {
    this.emit("event", event);
  }
}

export const eventBus = new ProxyEventBus();

import net from "net";
import { v4 as uuidv4 } from "uuid";
import { config } from "./config";
import { eventBus } from "./eventBus";
import type { StreamType } from "./types";

function log(...args: unknown[]) {
  // Simple logger; can be replaced with structured logging later
  console.log("[proxy]", ...args);
}

function emitToStreams(
  sessionId: string,
  direction: "client_to_server" | "server_to_client",
  chunkLength: number
) {
  const ts = new Date().toISOString();
  const streams: StreamType[] = ["network", "app", "visual"];

  for (const stream of streams) {
    eventBus.emitEvent({
      sessionId,
      ts,
      stream,
      direction,
      type: "raw_chunk",
      length: chunkLength,
    });
  }
}

const server = net.createServer((clientSocket) => {
  const sessionId = uuidv4();
  const clientAddress = `${clientSocket.remoteAddress}:${clientSocket.remotePort}`;

  log(`New session ${sessionId} from ${clientAddress}`);

  const upstreamSocket = net.connect(
    {
      host: config.upstreamHost,
      port: config.upstreamPort,
    },
    () => {
      log(`Session ${sessionId}: connected to upstream ${config.upstreamHost}:${config.upstreamPort}`);
    }
  );

  clientSocket.on("data", (chunk) => {
    emitToStreams(sessionId, "client_to_server", chunk.length);
    const ok = upstreamSocket.write(chunk);
    if (!ok) {
      log(`Session ${sessionId}: backpressure on upstream write`);
    }
  });

  upstreamSocket.on("data", (chunk) => {
    emitToStreams(sessionId, "server_to_client", chunk.length);
    const ok = clientSocket.write(chunk);
    if (!ok) {
      log(`Session ${sessionId}: backpressure on client write`);
    }
  });

  const closeSession = (why: string) => {
    log(`Session ${sessionId} closing: ${why}`);
    clientSocket.destroy();
    upstreamSocket.destroy();
  };

  clientSocket.on("error", (err) => {
    log(`Session ${sessionId} client error:`, err.message);
    closeSession("client_error");
  });

  upstreamSocket.on("error", (err) => {
    log(`Session ${sessionId} upstream error:`, err.message);
    closeSession("upstream_error");
  });

  clientSocket.on("close", () => {
    log(`Session ${sessionId}: client closed`);
    upstreamSocket.end();
  });

  upstreamSocket.on("close", () => {
    log(`Session ${sessionId}: upstream closed`);
    clientSocket.end();
  });
});

server.on("error", (err) => {
  log("Server error:", err.message);
});

server.listen(config.listenPort, config.listenHost, () => {
  log(
    `Proxy listening on ${config.listenHost}:${config.listenPort} -> ${config.upstreamHost}:${config.upstreamPort}`
  );
});

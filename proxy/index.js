const net = require("net");
const http = require("http");
const { v4: uuidv4 } = require("uuid");
require("dotenv").config();
console.log("Environment:", {
  listenPort: process.env.PROXY_LISTEN_PORT,
  upstreamHost: process.env.UPSTREAM_HOST,
  upstreamPort: process.env.UPSTREAM_PORT,
  honeypotPort: process.env.HONEYPOT_PORT,
});
const axios = require("axios");
const fs = require("fs");
const path = require("path");


function requireEnv(name, defaultValue) {
  const value = process.env[name] ?? defaultValue;
  if (!value) {
    throw new Error(`Missing required environment variable ${name}`);
  }
  return value;
}

const config = {
  listenHost: process.env.PROXY_LISTEN_HOST || "0.0.0.0",
  listenPort: Number(requireEnv("PROXY_LISTEN_PORT", "5900")),
  upstreamHost: requireEnv("UPSTREAM_HOST", "127.0.0.1"),
  upstreamPort: Number(requireEnv("UPSTREAM_PORT", "5901")),
  detectorEndpoint: process.env.DETECTOR_ENDPOINT || "",
  adminPort: Number(process.env.PROXY_ADMIN_PORT || "8000"),
  honeypotHost: process.env.HONEYPOT_HOST || process.env.UPSTREAM_HOST || "127.0.0.1",
  honeypotPort: Number(process.env.HONEYPOT_PORT || process.env.UPSTREAM_PORT || "5902"),
};

function log(...args) {
  console.log("[proxy]", ...args);
}

function ensureNetworkDir(sessionId) {
  const baseDir = path.join(__dirname, "data", sessionId, "network");
  fs.mkdirSync(baseDir, { recursive: true });
  return baseDir;
}

function persistNetworkChunk(sessionId, direction, chunk) {
  try {
    if (!chunk || !chunk.length) {
      return;
    }
    const dir = ensureNetworkDir(sessionId);
    const ts = new Date().toISOString().replace(/[:.]/g, "-");
    const filename = `packet_${direction}_${ts}_${chunk.length}.bin`;
    const dest = path.join(dir, filename);
    // For MVP we store the raw bytes as-is.
    fs.writeFileSync(dest, chunk);
  } catch (e) {
    log("failed to persist network chunk for session", sessionId, e.message);
  }
}

function sendEvent(event) {
  if (!config.detectorEndpoint) {
    // No detector endpoint configured yet; just log the event shape.
    log("event", event);
    return;
  }

  // Fire-and-forget HTTP POST; we don't await inside the hot path.
  axios
    .post(config.detectorEndpoint, event)
    .catch((err) => {
      log("failed to send event", err.message);
    });
}

function emitToStreams(sessionId, direction, chunkLength) {
  const ts = new Date().toISOString();
  const streams = ["network_stream", "app_stream", "visual_stream"];

  streams.forEach((stream) => {
    const event = {
      session_id: sessionId,
      ts,
      stream,
      direction,
      type: "raw_chunk",
      length: chunkLength,
    };
    sendEvent(event);
  });
}

// Track active sessions so the admin HTTP API can terminate or switch them.
// sessionId -> { clientSocket, upstreamSocket, deception }
const sessions = new Map();

function attachUpstreamHandlers(sessionId, clientSocket, upstreamSocket) {
  upstreamSocket.on("data", (chunk) => {
    // Persist network meta for server_to_client traffic.
    persistNetworkChunk(sessionId, "server_to_client", chunk);
    emitToStreams(sessionId, "server_to_client", chunk.length);
    const ok = clientSocket.write(chunk);
    if (!ok) {
      log(`Session ${sessionId}: backpressure on client write`);
    }
  });

  upstreamSocket.on("error", (err) => {
    log(`Session ${sessionId} upstream error:`, err.message);
    const entry = sessions.get(sessionId);
    if (entry) {
      entry.clientSocket.destroy();
      entry.upstreamSocket.destroy();
      sessions.delete(sessionId);
    }
  });

  upstreamSocket.on("close", () => {
    log(`Session ${sessionId}: upstream closed`);
    clientSocket.end();
    sessions.delete(sessionId);
  });
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
      log(
        `Session ${sessionId}: connected to upstream ${config.upstreamHost}:${config.upstreamPort}`
      );
    }
  );

  // Store sockets for admin control.
  sessions.set(sessionId, { clientSocket, upstreamSocket, deception: false });

  attachUpstreamHandlers(sessionId, clientSocket, upstreamSocket);

  clientSocket.on("data", (chunk) => {
    // Persist network meta for client_to_server traffic.
    persistNetworkChunk(sessionId, "client_to_server", chunk);
    emitToStreams(sessionId, "client_to_server", chunk.length);
    const entry = sessions.get(sessionId);
    if (!entry) {
      return;
    }
    const ok = entry.upstreamSocket.write(chunk);
    if (!ok) {
      log(`Session ${sessionId}: backpressure on upstream write`);
    }
  });

  const closeSession = (why) => {
    log(`Session ${sessionId} closing: ${why}`);
    clientSocket.destroy();
    upstreamSocket.destroy();
    sessions.delete(sessionId);
  };

  clientSocket.on("error", (err) => {
    log(`Session ${sessionId} client error:`, err.message);
    closeSession("client_error");
  });

  clientSocket.on("close", () => {
    log(`Session ${sessionId}: client closed`);
    upstreamSocket.end();
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

// --- Admin HTTP API ---------------------------------------------------------

const adminServer = http.createServer((req, res) => {
  if (req.method === "POST" && req.url === "/admin/kill-session") {
    let body = "";
    req.on("data", (chunk) => {
      body += chunk.toString();
    });
    req.on("end", () => {
      try {
        const data = JSON.parse(body || "{}");
        const sessionId = data.session_id;

        if (!sessionId) {
          res.statusCode = 400;
          res.setHeader("Content-Type", "application/json");
          res.end(JSON.stringify({ error: "session_id is required" }));
          return;
        }

        const entry = sessions.get(sessionId);
        if (!entry) {
          res.statusCode = 404;
          res.setHeader("Content-Type", "application/json");
          res.end(JSON.stringify({ error: "session not found" }));
          return;
        }

        // Terminate sockets immediately.
        try {
          entry.clientSocket.destroy();
          entry.upstreamSocket.destroy();
        } catch (e) {
          // ignore, we'll still consider the session terminated
        }
        sessions.delete(sessionId);
        log(`Session ${sessionId} terminated via Response Engine.`);

        res.statusCode = 200;
        res.setHeader("Content-Type", "application/json");
        res.end(JSON.stringify({ status: "terminated" }));
      } catch (err) {
        res.statusCode = 400;
        res.setHeader("Content-Type", "application/json");
        res.end(JSON.stringify({ error: "invalid JSON" }));
      }
    });
  } else if (req.method === "POST" && req.url === "/admin/activate-deception") {
    let body = "";
    req.on("data", (chunk) => {
      body += chunk.toString();
    });
    req.on("end", () => {
      try {
        const data = JSON.parse(body || "{}");
        const sessionId = data.session_id;

        if (!sessionId) {
          res.statusCode = 400;
          res.setHeader("Content-Type", "application/json");
          res.end(JSON.stringify({ error: "session_id is required" }));
          return;
        }

        const entry = sessions.get(sessionId);
        if (!entry) {
          res.statusCode = 404;
          res.setHeader("Content-Type", "application/json");
          res.end(JSON.stringify({ error: "session not found" }));
          return;
        }

        if (entry.deception) {
          res.statusCode = 200;
          res.setHeader("Content-Type", "application/json");
          res.end(JSON.stringify({ status: "deception_already_active" }));
          return;
        }

        // Connect to honeypot and swap upstream socket.
        const newUpstream = net.connect(
          {
            host: config.honeypotHost,
            port: config.honeypotPort,
          },
          () => {
            log(
              `Session ${sessionId}: switched to honeypot ${config.honeypotHost}:${config.honeypotPort}`
            );
          }
        );

        // Attach handlers for new upstream.
        attachUpstreamHandlers(sessionId, entry.clientSocket, newUpstream);

        try {
          entry.upstreamSocket.destroy();
        } catch (e) {
          // ignore
        }
        entry.upstreamSocket = newUpstream;
        entry.deception = true;

        log(`Deception mode enabled for session ${sessionId}.`);

        res.statusCode = 200;
        res.setHeader("Content-Type", "application/json");
        res.end(JSON.stringify({ status: "deception_active" }));
      } catch (err) {
        res.statusCode = 400;
        res.setHeader("Content-Type", "application/json");
        res.end(JSON.stringify({ error: "invalid JSON" }));
      }
    });
  } else {
    res.statusCode = 404;
    res.setHeader("Content-Type", "application/json");
    res.end(JSON.stringify({ error: "not found" }));
  }
});

adminServer.listen(config.adminPort, () => {
  log(`Admin API listening on 0.0.0.0:${config.adminPort}`);
});

import dotenv from "dotenv";

dotenv.config();

function requireEnv(name: string, defaultValue?: string): string {
  const value = process.env[name] ?? defaultValue;
  if (!value) {
    throw new Error(`Missing required environment variable ${name}`);
  }
  return value;
}

export const config = {
  listenHost: process.env.PROXY_LISTEN_HOST ?? "0.0.0.0",
  listenPort: Number(requireEnv("PROXY_LISTEN_PORT", "5900")),
  upstreamHost: requireEnv("UPSTREAM_HOST", "127.0.0.1"),
  upstreamPort: Number(requireEnv("UPSTREAM_PORT", "5901")),
  logLevel: process.env.LOG_LEVEL ?? "info",
};

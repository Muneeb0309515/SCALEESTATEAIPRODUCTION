import { spawn } from "node:child_process";

const port = process.env.PORT || "3000";
const api = spawn("python3", ["-m", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", "8000"], { stdio: ["ignore", "ignore", "pipe"] });
api.stderr.on("data", (buffer) => {
  const output = String(buffer);
  if (!output.includes("Uvicorn running on")) process.stderr.write(`[api] ${output}`);
});
const next = spawn("pnpm", ["exec", "next", "dev", "--port", port], { stdio: "inherit", env: process.env });
const stop = () => { api.kill("SIGTERM"); next.kill("SIGTERM"); };
process.on("SIGINT", stop); process.on("SIGTERM", stop);
next.on("exit", (code) => { api.kill("SIGTERM"); process.exit(code ?? 0); });

import http from "node:http";
import { spawn } from "node:child_process";

const port = Number(process.env.PORT || 3000);
const apiPort = 8000;
const webPort = 3001;
const api = spawn("python3", ["-m", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", String(apiPort)], { stdio: "inherit" });
const web = spawn("pnpm", ["exec", "next", "start", "--port", String(webPort)], { stdio: "inherit", env: process.env });
const stop = () => { api.kill("SIGTERM"); web.kill("SIGTERM"); };
process.on("SIGINT", stop); process.on("SIGTERM", stop);
http.createServer((request, response) => {
  const target = request.url?.startsWith("/api/") || request.url === "/health" ? apiPort : webPort;
  const proxy = http.request({ hostname: "127.0.0.1", port: target, path: request.url, method: request.method, headers: request.headers }, (upstream) => { response.writeHead(upstream.statusCode ?? 502, upstream.headers); upstream.pipe(response); });
  proxy.on("error", () => { response.writeHead(503, { "content-type": "application/json" }); response.end(JSON.stringify({ detail: "Service is starting or unavailable" })); });
  request.pipe(proxy);
}).listen(port);

import type { NextConfig } from "next";

const apiOrigin = process.env.API_INTERNAL_URL ?? "http://127.0.0.1:8000";
const nextConfig: NextConfig = {
  allowedDevOrigins: ["127.0.0.1", "localhost", "3000-iz9chabu4d2hf544lzxnj-e1a973e9.us3.manus.computer", "3000-ifk2c0egk8r030vh4b39k-2c723fe6.us1.manus.computer"],
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${apiOrigin}/api/:path*` }, { source: "/health", destination: `${apiOrigin}/health` }];
  },
};

export default nextConfig;

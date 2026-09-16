import path from "node:path";
import type { NextConfig } from "next";

const internalApi = process.env.INTERNAL_API_URL?.replace(/\/$/, "");

const nextConfig: NextConfig = {
  outputFileTracingRoot: path.join(__dirname, "../.."),
  transpilePackages: ["@repo/auth"],
  async rewrites() {
    if (!internalApi) return [];
    return [
      {
        source: "/backend-api/:path*",
        destination: `${internalApi}/:path*`,
      },
    ];
  },
};

export default nextConfig;

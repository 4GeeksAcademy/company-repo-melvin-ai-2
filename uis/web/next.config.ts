import path from "node:path";
import { fileURLToPath } from "node:url";
import type { NextConfig } from "next";

const rootDir = path.dirname(fileURLToPath(import.meta.url));

const nextConfig: NextConfig = {
  outputFileTracingRoot: path.join(rootDir, "../.."),
  transpilePackages: ["@repo/auth"],
  turbopack: {
    root: path.join(rootDir, "../.."),
  },
};

export default nextConfig;

import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  transpilePackages: ["@mitonexus/shared-types"],
  experimental: {
    typedRoutes: true,
  },
};

export default nextConfig;

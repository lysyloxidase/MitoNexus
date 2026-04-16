import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  transpilePackages: ["@mitonexus/shared-types"],
  experimental: {
    typedRoutes: true,
  },
  async rewrites() {
    const apiProxyUrl = process.env.MITONEXUS_API_PROXY_URL ?? "http://localhost:8000";
    return [
      {
        source: "/api/v1/:path*",
        destination: `${apiProxyUrl}/api/v1/:path*`,
      },
    ];
  },
};

export default nextConfig;

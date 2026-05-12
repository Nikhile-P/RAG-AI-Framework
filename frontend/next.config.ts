import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      // Note: POST /api/chat is handled by src/app/api/chat/route.ts (long timeout).
      // Remaining /api/* paths still proxy here:
      {
        source: "/api/:path*",
        destination: "http://127.0.0.1:8000/api/:path*", // Fixed port here
      },
    ];
  },
};

export default nextConfig;
/** @type {import('next').NextConfig} */
const apiInternal =
  process.env.API_INTERNAL_URL || process.env.MULTISCALE_API_URL || "http://localhost:8000";

const nextConfig = {
  output: "standalone",
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${apiInternal}/api/:path*`,
      },
      {
        source: "/health/:path*",
        destination: `${apiInternal}/health/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;

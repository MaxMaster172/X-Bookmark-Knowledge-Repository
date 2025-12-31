import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Required for Transformers.js ONNX runtime (browser-based embeddings)
  webpack: (config) => {
    config.resolve.alias = {
      ...config.resolve.alias,
      sharp$: false,
      "onnxruntime-node$": false,
    };
    return config;
  },

  // Empty turbopack config to acknowledge we have webpack config
  // Turbopack is used for dev, webpack for build
  turbopack: {},

  // Allow images from Twitter CDN
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "pbs.twimg.com" },
      { protocol: "https", hostname: "video.twimg.com" },
      { protocol: "https", hostname: "abs.twimg.com" },
    ],
  },

  // Suppress hydration warnings for theme switching
  reactStrictMode: true,
};

export default nextConfig;

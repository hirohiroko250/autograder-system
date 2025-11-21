/** @type {import('next').NextConfig} */
const nextConfig = {
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  images: { unoptimized: true },
  // Hydration警告を抑制
  reactStrictMode: false,
  // 開発環境での不要な警告を抑制
  onDemandEntries: {
    maxInactiveAge: 25 * 1000,
    pagesBufferLength: 2,
  },
  // CSS preload警告を抑制
  webpack: (config, { dev, isServer }) => {
    if (dev && !isServer) {
      // CSSのpreload警告を抑制
      config.optimization = {
        ...config.optimization,
        splitChunks: {
          ...config.optimization.splitChunks,
          cacheGroups: {
            ...config.optimization.splitChunks?.cacheGroups,
            styles: {
              name: 'styles',
              test: /\.css$/,
              chunks: 'all',
              enforce: true,
            },
          },
        },
      };
    }
    return config;
  },
  // 開発サーバー設定
  devIndicators: {
    buildActivity: false,
    buildActivityPosition: 'bottom-right',
  },
  swcMinify: false,
};

module.exports = nextConfig;

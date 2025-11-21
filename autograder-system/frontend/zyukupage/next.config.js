/** @type {import('next').NextConfig} */
const nextConfig = {
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  images: { unoptimized: true },
  webpack: (config, { isServer }) => {
    // Increase timeout for CSS loading
    config.watchOptions = {
      ...config.watchOptions,
      poll: 1000,
      aggregateTimeout: 300
    }
    
    return config
  },
  // Disable strict mode to avoid some timeout issues
  reactStrictMode: false,
  // Increase build timeout
  staticPageGenerationTimeout: 120,
  // 開発環境での不要な警告を抑制
  onDemandEntries: {
    maxInactiveAge: 25 * 1000,
    pagesBufferLength: 2,
  },
  // SWC minify が一部依存のテンプレート文字列を壊すため無効化
  swcMinify: false,
};

module.exports = nextConfig;

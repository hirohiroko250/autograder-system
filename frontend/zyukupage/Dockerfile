# ビルドステージ
FROM node:18-alpine AS builder

WORKDIR /app

# 依存関係をインストール
COPY package*.json ./
RUN npm ci

# アプリケーションコードをコピー
COPY . .

# ビルド時の環境変数を受け取る
ARG NEXT_PUBLIC_API_BASE_URL
ARG NEXT_PUBLIC_CLASSROOM_URL
ENV NEXT_PUBLIC_API_BASE_URL=${NEXT_PUBLIC_API_BASE_URL}
ENV NEXT_PUBLIC_CLASSROOM_URL=${NEXT_PUBLIC_CLASSROOM_URL}

# Next.jsアプリケーションをビルド
RUN npm run build

# 実行ステージ
FROM node:18-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production

# 必要なファイルのみをコピー
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

# ポート3000を公開
EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# アプリケーションを起動
CMD ["node", "server.js"]

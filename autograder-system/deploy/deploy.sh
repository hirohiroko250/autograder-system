#!/bin/bash
set -e

# デプロイスクリプト
# 使用方法: ./deploy.sh [production|staging]

ENVIRONMENT=${1:-production}
PROJECT_ROOT="/home/skyuser/Documents/an 小学生テスト"

echo "=========================================="
echo "🚀 デプロイ開始: $ENVIRONMENT"
echo "=========================================="

# プロジェクトディレクトリに移動
cd "$PROJECT_ROOT"

# 最新のコードを取得
echo "📥 最新のコードを取得中..."
git pull origin main

# 環境変数の設定
if [ "$ENVIRONMENT" = "production" ]; then
    export ENV_FILE=".env.production"
else
    export ENV_FILE=".env"
fi

echo "🔧 環境: $ENVIRONMENT ($ENV_FILE)"

# Dockerコンテナの再起動
echo "🐳 Dockerコンテナを再起動中..."
cd "$PROJECT_ROOT/autograder-system"
docker-compose down
docker-compose up -d --build

# データベースマイグレーション
echo "📊 データベースマイグレーションを実行中..."
docker-compose exec -T backend python manage.py migrate --noinput

# 静的ファイルの収集
echo "📦 静的ファイルを収集中..."
docker-compose exec -T backend python manage.py collectstatic --noinput

# コンテナの状態確認
echo "✅ コンテナの状態確認..."
docker-compose ps

echo "=========================================="
echo "✨ デプロイ完了！"
echo "=========================================="

#!/bin/bash

# 🐳 全国学力向上テスト Docker 起動スクリプト

echo "🚀 Docker環境を起動しています..."

# .env.productionを.envとしてコピー
cp .env.production .env

# Docker Composeでサービスを起動
echo "📦 Dockerコンテナをビルド・起動中..."
docker-compose up --build -d

echo "⏳ データベースの初期化を待機中..."
sleep 10

# データベースのマイグレーション実行
echo "🗄️  データベースマイグレーション実行中..."
docker-compose exec backend python manage.py migrate

# 既存のデータをインポート（オプション）
echo "📥 データベースにバックアップデータをインポートしますか？ (y/n)"
read -r import_data
if [ "$import_data" = "y" ]; then
    if [ -f "backup_*.json" ]; then
        echo "📊 データインポート中..."
        docker-compose exec backend python manage.py loaddata /app/backup_*.json
    else
        echo "⚠️  バックアップファイルが見つかりません"
    fi
fi

# サービス状態を表示
echo "📊 サービス状態:"
docker-compose ps

echo "✅ 起動完了!"
echo ""
echo "🌐 アクセス先:"
echo "   塾管理画面:    http://localhost:3000"
echo "   教室管理画面:  http://localhost:3001"
echo "   API:           http://localhost:8000"
echo "   Admin:         http://localhost:8000/admin"
echo ""
echo "🛑 停止する場合: docker-compose down"
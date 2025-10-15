#!/bin/bash
# システム状況確認スクリプト

echo "=== Docker コンテナ状況 ==="
docker compose ps

echo -e "\n=== 使用中の Django 設定ファイル ==="
docker exec autograder-system-backend-1 python -c "import os; print(Settings:, os.environ.get(DJANGO_SETTINGS_MODULE, autograder.settings))"

echo -e "\n=== CSRF ミドルウェア状況 ==="
docker exec autograder-system-backend-1 python -c "
from django.conf import settings
middleware = getattr(settings, MIDDLEWARE, [])
csrf_enabled = django.middleware.csrf.CsrfViewMiddleware in middleware
print(CSRF Middleware:, Enabled if csrf_enabled else Disabled)
"

echo -e "\n=== SSL 証明書ファイル ==="
ls -la /root/autograder-system/ssl/

echo -e "\n=== 最新のバックエンドログ ==="
docker logs autograder-system-backend-1 --tail 3

echo -e "\n=== システム正常性チェック完了 ==="

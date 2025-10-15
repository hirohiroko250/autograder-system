# トラブルシューティングガイド

## 1. 設定変更が反映されない場合

### 確認事項
```bash
# 1. どの設定ファイルが使われているか確認
docker exec autograder-system-backend-1 python -c "import os; print(DJANGO_SETTINGS_MODULE:, os.environ.get(DJANGO_SETTINGS_MODULE, autograder.settings))"

# 2. 設定ファイルの内容確認
docker exec autograder-system-backend-1 cat /app/autograder/settings.py | grep -A 5 -B 5 MIDDLEWARE

# 3. コンテナ再起動
docker compose restart backend
```

## 2. CSRF エラーの対処法

### 一時的な解決方法
```python
# settings.py でCSRFミドルウェアを無効化
MIDDLEWARE = [
    corsheaders.middleware.CorsMiddleware,
    django.middleware.security.SecurityMiddleware,
    django.contrib.sessions.middleware.SessionMiddleware,
    django.middleware.common.CommonMiddleware,
    # django.middleware.csrf.CsrfViewMiddleware,  # コメントアウト
    django.contrib.auth.middleware.AuthenticationMiddleware,
    django.contrib.messages.middleware.MessageMiddleware,
    django.middleware.clickjacking.XFrameOptionsMiddleware,
]
```

### 本格的な解決方法
```python
# CSRF_TRUSTED_ORIGINS に全ドメインを追加
CSRF_TRUSTED_ORIGINS = [
    "https://kouzyoutest.com",
    "https://www.kouzyoutest.com",
    "https://162.43.55.80",
    "http://162.43.55.80",
]
```

## 3. SSL/HTTPS 設定

### 証明書の確認
```bash
# SSL証明書ファイルの存在確認
ls -la /root/autograder-system/ssl/

# nginx設定の確認
docker exec autograder-system-nginx-1 nginx -t
```

## 4. ログ確認方法

```bash
# バックエンドログ
docker logs autograder-system-backend-1 --tail 20

# nginxログ
docker logs autograder-system-nginx-1 --tail 20

# 全コンテナステータス
docker compose ps
```

## 5. よくある問題と解決法

### 問題: 管理画面にログインできない
- **原因**: CSRF検証エラー
- **解決**: CSRFミドルウェア無効化または CSRF_TRUSTED_ORIGINS 設定

### 問題: 設定変更が反映されない
- **原因**: 異なる設定ファイルが使われている
- **解決**: 実際に使用されている設定ファイルを特定して修正

### 問題: HTTPSでアクセスできない
- **原因**: SSL証明書の設定ミス
- **解決**: 証明書ファイルの確認とnginx設定の見直し

## 6. 緊急時の対処

### 完全リセット
```bash
cd /root/autograder-system
docker compose down
docker compose up -d --build
```

### バックアップから復元
```bash
cd /root/autograder-system
./backup_db.sh  # バックアップ実行
# 問題発生時
docker exec autograder-system-backend-1 python manage.py loaddata /path/to/backup.json
```

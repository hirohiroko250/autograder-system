# 全国学力向上テストシステム - バックエンド運用マニュアル

## 目次
1. [システム概要](#システム概要)
2. [日常運用](#日常運用)
3. [バックアップ・復元](#バックアップ復元)
4. [トラブルシューティング](#トラブルシューティング)
5. [メンテナンス](#メンテナンス)
6. [監視とログ](#監視とログ)
7. [緊急時対応](#緊急時対応)

---

## システム概要

### アーキテクチャ
- **バックエンド**: Django 4.2.7 + Django REST Framework
- **データベース**: PostgreSQL 14
- **Webサーバー**: Gunicorn + Nginx
- **フロントエンド**: Next.js (2つのアプリケーション)
- **デプロイ**: Docker Compose

### サーバー情報
- **ドメイン**: kouzyoutest.com
- **管理画面**: https://kouzyoutest.com/admin
- **教室管理**: https://classroom.kouzyoutest.com
- **サーバーIP**: root@kouzyoutest.com

### 主要なディレクトリ構造
```
/root/autograder-system/
├── backend/                 # Djangoバックエンド
│   ├── accounts/           # ユーザー認証
│   ├── students/           # 生徒管理
│   ├── schools/            # 学校・教室管理
│   ├── scores/             # 成績管理
│   ├── reports/            # レポート生成
│   ├── static/             # 静的ファイル
│   ├── templates/          # HTMLテンプレート
│   ├── logs/               # ログファイル
│   └── db.sqlite3          # 開発用DB
├── frontend/               # フロントエンド
│   ├── classroom/          # 教室管理画面
│   └── zyukupage/         # 塾向けページ
├── deploy/                 # デプロイ設定
│   └── nginx.conf         # Nginx設定
├── ssl/                    # SSL証明書
├── logs/                   # アプリケーションログ
└── docker-compose.yml     # Docker設定
```

---

## 日常運用

### システム起動・停止

#### 全サービス起動
```bash
cd /root/autograder-system
docker compose up -d
```

#### 全サービス停止
```bash
docker compose down
```

#### 特定サービスの再起動
```bash
# バックエンドのみ
docker compose restart backend

# フロントエンド（classroom）のみ
docker compose restart frontend-classroom

# データベースのみ
docker compose restart db

# Nginxのみ
docker compose restart nginx
```

#### サービス状態確認
```bash
docker compose ps
docker compose logs -f backend  # リアルタイムログ表示
```

### データベース操作

#### Django管理コマンド実行
```bash
# マイグレーション実行
docker compose exec backend python manage.py migrate

# スーパーユーザー作成
docker compose exec backend python manage.py createsuperuser

# 静的ファイル収集
docker compose exec backend python manage.py collectstatic --noinput

# データベースシェル
docker compose exec backend python manage.py dbshell
```

#### PostgreSQLに直接接続
```bash
docker compose exec db psql -U autograder_user -d autograder_db
```

よく使うSQLクエリ:
```sql
-- テーブル一覧
\dt

-- 生徒数確認
SELECT COUNT(*) FROM students_student;

-- テスト結果数確認
SELECT COUNT(*) FROM scores_testresult;

-- 最新の登録生徒
SELECT * FROM students_student ORDER BY created_at DESC LIMIT 10;
```

### コンテナ内部アクセス

#### バックエンドコンテナ
```bash
docker compose exec backend bash
# または
docker compose exec backend sh
```

#### データベースコンテナ
```bash
docker compose exec db bash
```

---

## バックアップ・復元

### データベースバックアップ

#### 手動バックアップ（推奨：毎日実施）
```bash
# バックアップディレクトリ作成
mkdir -p /root/backups

# バックアップ実行（日付付き）
docker compose exec db pg_dump -U autograder_user autograder_db > /root/backups/db_backup_$(date +%Y%m%d_%H%M%S).sql

# 圧縮バックアップ
docker compose exec db pg_dump -U autograder_user autograder_db | gzip > /root/backups/db_backup_$(date +%Y%m%d_%H%M%S).sql.gz
```

#### 自動バックアップスクリプト
```bash
# /root/backup_db.sh を作成
cat > /root/backup_db.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/root/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/db_backup_${DATE}.sql.gz"

mkdir -p ${BACKUP_DIR}

cd /root/autograder-system
docker compose exec -T db pg_dump -U autograder_user autograder_db | gzip > ${BACKUP_FILE}

# 7日以上古いバックアップを削除
find ${BACKUP_DIR} -name "db_backup_*.sql.gz" -mtime +7 -delete

echo "Backup completed: ${BACKUP_FILE}"
EOF

chmod +x /root/backup_db.sh

# cronで毎日3:00に実行
(crontab -l 2>/dev/null; echo "0 3 * * * /root/backup_db.sh") | crontab -
```

### データベース復元

#### バックアップからの復元
```bash
# 復元前にサービス停止
docker compose stop backend

# データベース復元
gunzip -c /root/backups/db_backup_YYYYMMDD_HHMMSS.sql.gz | docker compose exec -T db psql -U autograder_user autograder_db

# または圧縮なしの場合
docker compose exec -T db psql -U autograder_user autograder_db < /root/backups/db_backup_YYYYMMDD_HHMMSS.sql

# サービス再起動
docker compose start backend
```

### メディアファイル・静的ファイルのバックアップ

```bash
# メディアファイル（アップロードされたファイル）
tar -czf /root/backups/media_$(date +%Y%m%d).tar.gz -C /root/autograder-system/backend mediafiles/

# 静的ファイル
tar -czf /root/backups/static_$(date +%Y%m%d).tar.gz -C /root/autograder-system/backend staticfiles/
```

---

## トラブルシューティング

### よくある問題と解決方法

#### 1. サービスが起動しない

**症状**: `docker compose up -d` でエラー

**確認項目**:
```bash
# ポート使用状況確認
netstat -tlnp | grep :80
netstat -tlnp | grep :443

# ディスク容量確認
df -h

# メモリ使用状況
free -h

# Dockerログ確認
docker compose logs backend
docker compose logs db
```

**解決方法**:
```bash
# コンテナとネットワークをクリーンアップ
docker compose down
docker system prune -f

# 再起動
docker compose up -d
```

#### 2. データベース接続エラー

**症状**: "could not connect to server" エラー

**確認項目**:
```bash
# DBコンテナの状態確認
docker compose ps db

# DBログ確認
docker compose logs db
```

**解決方法**:
```bash
# DBコンテナ再起動
docker compose restart db

# 接続テスト
docker compose exec backend python manage.py dbshell
```

#### 3. 静的ファイルが表示されない

**症状**: CSSやJSが読み込まれない

**解決方法**:
```bash
# 静的ファイル再収集
docker compose exec backend python manage.py collectstatic --noinput

# パーミッション確認
docker compose exec backend ls -la /app/staticfiles

# Nginx再起動
docker compose restart nginx
```

#### 4. マイグレーションエラー

**症状**: "Migration not applied" エラー

**解決方法**:
```bash
# マイグレーション状態確認
docker compose exec backend python manage.py showmigrations

# マイグレーション実行
docker compose exec backend python manage.py migrate

# 偽適用（最終手段）
docker compose exec backend python manage.py migrate --fake app_name migration_name
```

#### 5. ディスク容量不足

**症状**: "No space left on device"

**確認・対処**:
```bash
# ディスク使用量確認
df -h

# 大きなファイル検索
du -h /root | sort -h | tail -20

# Dockerイメージ・コンテナ削除
docker system prune -a --volumes

# 古いログ削除
find /root/autograder-system/logs -name "*.log" -mtime +30 -delete
find /root/backups -name "*.sql.gz" -mtime +30 -delete
```

#### 6. メモリ不足

**症状**: サービスが頻繁にクラッシュ

**確認**:
```bash
# メモリ使用状況
free -h
docker stats
```

**対処**:
```bash
# 不要なコンテナ停止
docker ps -a
docker stop <container_id>

# スワップ領域追加（必要に応じて）
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

---

## メンテナンス

### 定期メンテナンス作業

#### 毎日
- [ ] バックアップ実行確認
- [ ] ログファイルサイズ確認
- [ ] エラーログ確認

#### 毎週
- [ ] ディスク容量確認
- [ ] データベース整合性チェック
- [ ] 不要なDockerイメージ削除

#### 毎月
- [ ] SSL証明書有効期限確認
- [ ] セキュリティアップデート適用
- [ ] パフォーマンス分析
- [ ] 古いバックアップ削除

### SSL証明書更新

```bash
# 証明書確認
openssl x509 -in /root/autograder-system/ssl/cert.pem -noout -dates

# Let's Encrypt更新（certbot使用）
certbot renew --dry-run  # テスト実行
certbot renew             # 実際の更新

# 証明書配置
cp /etc/letsencrypt/live/kouzyoutest.com/fullchain.pem /root/autograder-system/ssl/cert.pem
cp /etc/letsencrypt/live/kouzyoutest.com/privkey.pem /root/autograder-system/ssl/key.pem

# Nginx再起動
docker compose restart nginx
```

### Djangoパッケージアップデート

```bash
# バックエンドコンテナに入る
docker compose exec backend bash

# 現在のバージョン確認
pip list

# requirements.txtのバージョン更新（慎重に）
# vi /app/requirements.txt

# パッケージ更新
pip install -r requirements.txt --upgrade

# テスト実行
python manage.py test

# マイグレーション確認
python manage.py makemigrations --dry-run
python manage.py migrate

# サービス再起動
exit
docker compose restart backend
```

### データベース最適化

```bash
# PostgreSQL VACUUM実行
docker compose exec db psql -U autograder_user -d autograder_db -c "VACUUM ANALYZE;"

# データベースサイズ確認
docker compose exec db psql -U autograder_user -d autograder_db -c "SELECT pg_size_pretty(pg_database_size('autograder_db'));"

# 不要なデータ削除（古いログなど）
docker compose exec backend python manage.py shell
>>> from django.utils import timezone
>>> from datetime import timedelta
>>> cutoff_date = timezone.now() - timedelta(days=90)
>>> # 例: 90日以上前のログを削除
```

---

## 監視とログ

### ログファイルの場所

```
/root/autograder-system/logs/          # アプリケーションログ
/root/autograder-system/backend/autograder.log  # Djangoログ
```

### ログ確認方法

#### リアルタイムログ監視
```bash
# バックエンド
docker compose logs -f backend

# データベース
docker compose logs -f db

# Nginx
docker compose logs -f nginx

# すべてのサービス
docker compose logs -f
```

#### ログファイル直接確認
```bash
# 最新のエラーログ
tail -f /root/autograder-system/backend/autograder.log

# エラー行のみ抽出
grep -i error /root/autograder-system/backend/autograder.log

# 日付範囲でフィルタ
grep "2025-10-09" /root/autograder-system/backend/autograder.log
```

### システムリソース監視

```bash
# CPU・メモリ使用率（リアルタイム）
docker stats

# ディスク使用状況
df -h

# ネットワーク接続
netstat -tulpn | grep LISTEN

# プロセス確認
top
htop  # インストールされている場合
```

### ログローテーション設定

```bash
# /etc/logrotate.d/autograder を作成
cat > /etc/logrotate.d/autograder << 'EOF'
/root/autograder-system/backend/autograder.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 root root
}

/root/autograder-system/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 644 root root
}
EOF
```

---

## 緊急時対応

### システムダウン時の対応フロー

#### 1. 状況確認（5分以内）
```bash
# サービス状態確認
docker compose ps

# ログ確認
docker compose logs --tail=100 backend
docker compose logs --tail=100 nginx

# リソース確認
free -h
df -h
```

#### 2. 緊急再起動（10分以内）
```bash
# 全サービス再起動
docker compose restart

# または完全再起動
docker compose down
docker compose up -d
```

#### 3. データベース復旧（必要時）
```bash
# 最新バックアップから復元
ls -lt /root/backups/*.sql.gz | head -1
gunzip -c /root/backups/db_backup_YYYYMMDD_HHMMSS.sql.gz | docker compose exec -T db psql -U autograder_user autograder_db
```

### データ破損時の対応

```bash
# 1. データベース整合性チェック
docker compose exec db psql -U autograder_user -d autograder_db
\d  # テーブル一覧確認
SELECT COUNT(*) FROM students_student;  # データ存在確認

# 2. バックアップから復元
# 上記「データベース復元」参照

# 3. Django整合性チェック
docker compose exec backend python manage.py check
docker compose exec backend python manage.py migrate --check
```

### セキュリティインシデント対応

#### 不正アクセス検知時
```bash
# 1. アクセスログ確認
docker compose logs nginx | grep -i "404\|403\|401"

# 2. 疑わしいIPをブロック
# /root/autograder-system/deploy/nginx.conf に追加
# deny 123.456.789.0;

# 3. パスワード変更
docker compose exec backend python manage.py changepassword <username>

# 4. セッション無効化
docker compose exec backend python manage.py shell
>>> from django.contrib.sessions.models import Session
>>> Session.objects.all().delete()
```

### エスカレーション連絡先

**緊急連絡先**:
- システム管理者: [連絡先記載]
- データベース管理者: [連絡先記載]
- 開発チーム: [連絡先記載]

---

## 付録

### 便利なコマンド集

```bash
# コンテナの完全クリーンアップ
docker compose down -v
docker system prune -a --volumes

# 特定のマイグレーションに戻る
docker compose exec backend python manage.py migrate app_name 0001

# データベースのダンプとリストア（ワンライナー）
docker compose exec db pg_dump -U autograder_user autograder_db | gzip > backup.sql.gz
gunzip -c backup.sql.gz | docker compose exec -T db psql -U autograder_user autograder_db

# Djangoシェルでのデータ確認
docker compose exec backend python manage.py shell
>>> from students.models import Student
>>> Student.objects.count()
>>> Student.objects.all()[:5]

# パフォーマンス分析
docker stats --no-stream
docker compose exec db psql -U autograder_user -d autograder_db -c "SELECT * FROM pg_stat_activity;"
```

### 環境変数一覧

主要な環境変数（`.env`ファイル）:
```
DJANGO_SECRET_KEY=your-secret-key
DEBUG=False
DATABASE_URL=postgresql://user:password@db:5432/autograder_db
ALLOWED_HOSTS=kouzyoutest.com,classroom.kouzyoutest.com
```

---

## バージョン履歴

| バージョン | 日付 | 変更内容 |
|----------|------|----------|
| 1.0 | 2025-10-09 | 初版作成 |

---

## 問い合わせ

システムに関する質問や問題が発生した場合は、以下に連絡してください：
- Email: [support@example.com]
- チケットシステム: [URL]

---

**最終更新**: 2025年10月9日

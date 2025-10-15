# 全国学力向上テスト Backend

Django REST API for 全国学力向上テスト - 塾向けテスト採点・管理システム

## 概要

- **Django 5.0** + **Django REST Framework**
- **PostgreSQL** データベース
- **JWT** 認証
- **Celery** + **Redis** 非同期処理
- **Excel** インポート/エクスポート
- **マルチテナント** (塾単位での完全分離)

## セットアップ

### 1. 仮想環境の作成・有効化

```bash
python -m venv autograder_env
source autograder_env/bin/activate  # Linux/Mac
# autograder_env\Scripts\activate  # Windows
```

### 2. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 3. 環境変数の設定

`.env` ファイルを編集してデータベース接続情報を設定

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
DB_NAME=autograder_pro
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432
```

### 4. データベース設定

```bash
# PostgreSQL データベース作成
createdb autograder_pro

# マイグレーション実行
python manage.py makemigrations
python manage.py migrate

# スーパーユーザー作成
python manage.py createsuperuser
```

### 5. サーバー起動

```bash
python manage.py runserver
```

## API エンドポイント

### 認証
- `POST /api/auth/login/` - ログイン
- `POST /api/auth/refresh/` - トークンリフレッシュ
- `POST /api/auth/change-password/` - パスワード変更

### 塾管理
- `GET /api/schools/` - 塾情報取得
- `POST /api/schools/{id}/create_classroom/` - 教室作成

### 教室管理
- `GET /api/classrooms/` - 教室一覧
- `POST /api/classrooms/{id}/reset_password/` - 教室パスワードリセット

### 生徒管理
- `GET /api/students/` - 生徒一覧
- `POST /api/students/` - 生徒作成
- `POST /api/students/import_students/` - 生徒一括インポート
- `GET /api/students/export_excel/` - 生徒一括エクスポート
- `GET /api/students/next_id/` - 次の生徒ID取得

## 開発用コマンド

```bash
# 初期データ作成
python manage.py init_data --demo

# テスト実行
python manage.py test

# Celery ワーカー起動
celery -A autograder worker --loglevel=info

# Redis 起動 (別ターミナル)
redis-server
```

## アーキテクチャ

### マルチテナント設計
- 塾 (School) 単位でのデータ完全分離
- JWT トークンに `school_id` / `classroom_id` を含める
- 権限制御とデータフィルタリング

### 主要機能
1. **ユーザー認証**: カスタムユーザーモデル + JWT
2. **データ管理**: 塾/教室/生徒/テスト/成績
3. **Excel連携**: 一括インポート/エクスポート
4. **締切制御**: テスト締切日による書き込み制限
5. **非同期処理**: PDF生成・メール送信

## ディレクトリ構成

```
backend/
├── autograder/          # プロジェクト設定
├── accounts/           # ユーザー認証
├── schools/            # 塾管理
├── classrooms/         # 教室管理
├── students/           # 生徒管理
├── tests/              # テスト・問題管理
├── scores/             # 成績管理
├── reports/            # 帳票生成
├── utils/              # 共通ユーティリティ
├── requirements.txt    # パッケージ依存関係
├── .env               # 環境変数
└── manage.py          # Django管理コマンド
```

## 本番デプロイ

```bash
# 静的ファイル収集
python manage.py collectstatic

# Gunicorn 起動
gunicorn autograder.wsgi:application --bind 0.0.0.0:8000
```
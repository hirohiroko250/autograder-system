# Python 3.11 ベースイメージ
FROM python:3.11-slim

# 作業ディレクトリを設定
WORKDIR /app

# システムパッケージの更新とインストール
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    postgresql-client \
    libpq-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# requirements.txtをコピーして依存関係をインストール
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー
COPY . /app/

# 静的ファイル用ディレクトリを作成
RUN mkdir -p /app/staticfiles
RUN mkdir -p /app/mediafiles

# 静的ファイルを収集（エラーを無視）
RUN python manage.py collectstatic --noinput --clear || true

# ポート8000を公開
EXPOSE 8000

# デフォルトコマンド
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
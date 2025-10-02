"""
Gunicorn設定ファイル
"""
import multiprocessing
import os
from pathlib import Path

# サーバーソケット
bind = "0.0.0.0:8000"
backlog = 2048

# ワーカープロセス（メモリ使用量を抑えるため最小限に）
workers = 1
worker_class = "sync"
worker_connections = 100
timeout = 30
keepalive = 2
max_requests = 1000
max_requests_jitter = 50

# ログ設定
loglevel = "info"
log_dir = os.environ.get("LOG_DIR", "/var/log/autograder")
os.makedirs(log_dir, exist_ok=True)
accesslog = f"{log_dir}/gunicorn_access.log"
errorlog = f"{log_dir}/gunicorn_error.log"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# プロセス設定
daemon = False
pidfile_dir = Path("/run/autograder")
pidfile_dir.mkdir(parents=True, exist_ok=True)
pidfile = str(pidfile_dir / "gunicorn.pid")

# Allow overriding the user/group via environment variables; default to root inside the container.
user = os.environ.get("GUNICORN_USER", "root")
group = os.environ.get("GUNICORN_GROUP", "root")
tmp_upload_dir = None

# セキュリティ
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# パフォーマンス
preload_app = True
worker_tmp_dir = "/dev/shm"

# 開発環境用設定
if os.environ.get('DEBUG', 'False').lower() == 'true':
    reload = True
    loglevel = "debug"
    daemon = False

"""
Gunicorn設定ファイル
"""
import multiprocessing
import os

# サーバーソケット
bind = "0.0.0.0:8000"
backlog = 2048

# ワーカープロセス
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2
max_requests = 1000
max_requests_jitter = 50

# ログ設定
loglevel = "info"
accesslog = "/var/log/autograder/gunicorn_access.log"
errorlog = "/var/log/autograder/gunicorn_error.log"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# プロセス設定
daemon = False
pidfile = "/run/autograder/gunicorn.pid"
user = "autograder"
group = "autograder"
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
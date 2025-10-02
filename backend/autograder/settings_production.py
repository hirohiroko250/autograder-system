"""
本番環境用Django設定
"""
from .settings import *
import os
from pathlib import Path

# 本番環境フラグ
DEBUG = False
ALLOWED_HOSTS = [
    '162.43.55.80',
    'localhost',
    '127.0.0.1',
    'autograder-system.com',  # 独自ドメインがある場合
    'kouzyoutest.xvps.jp',
    'classroom.kouzyoutest.xvps.jp',
    'kouzyoutest.com',
    'www.kouzyoutest.com',
    'classroom.kouzyoutest.com',
]

# セキュリティ設定
SECURE_SSL_REDIRECT = False  # HTTPSが設定された場合にTrueにする
SECURE_HSTS_SECONDS = 31536000 if SECURE_SSL_REDIRECT else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

# セッション・クッキー設定
SESSION_COOKIE_SECURE = SECURE_SSL_REDIRECT
CSRF_COOKIE_SECURE = SECURE_SSL_REDIRECT
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True

# データベース設定（本番用）
if os.environ.get('DATABASE_URL'):
    # PostgreSQL等の本番DB設定
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.parse(os.environ.get('DATABASE_URL'))
    }
else:
    # SQLite（開発・テスト用）
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db_production.sqlite3',
        }
    }

# 静的ファイル設定
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_ROOT = BASE_DIR / 'mediafiles'

# キャッシュ設定
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/1'),
    } if os.environ.get('REDIS_URL') else {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# ログディレクトリを確保
LOG_DIR = Path(os.environ.get('LOG_DIR', '/var/log/autograder'))
LOG_DIR.mkdir(parents=True, exist_ok=True)

# ログ設定（本番用）
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(LOG_DIR / 'django.log'),
            'maxBytes': 1024*1024*15,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(LOG_DIR / 'django_error.log'),
            'maxBytes': 1024*1024*15,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'WARNING',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['error_file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'autograder': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Email設定（本番用）
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER)

# CORS設定（本番用）
CORS_ALLOWED_ORIGINS = [
    "https://162.43.55.80",
    "http://162.43.55.80",
    "http://162.43.55.80:3000",
    "http://162.43.55.80:3001",
    "https://autograder-system.com",  # 独自ドメインがある場合
    "http://localhost:3000",  # フロントエンド開発用
    "http://localhost:3001",  # フロントエンド開発用（教室ページ）
    "https://kouzyoutest.xvps.jp",
    "https://classroom.kouzyoutest.xvps.jp",
    "https://kouzyoutest.com",
    "https://www.kouzyoutest.com",
    "https://classroom.kouzyoutest.com",
    "http://kouzyoutest.com",
    "http://www.kouzyoutest.com",
    "http://classroom.kouzyoutest.com",
]

CSRF_TRUSTED_ORIGINS += [
    "https://kouzyoutest.xvps.jp",
    "https://classroom.kouzyoutest.xvps.jp",
    "https://kouzyoutest.com",
    "https://www.kouzyoutest.com",
    "https://classroom.kouzyoutest.com",
    "http://kouzyoutest.com",
    "http://www.kouzyoutest.com",
    "http://classroom.kouzyoutest.com",
]

# 管理者設定
ADMINS = [
    ('Admin', os.environ.get('ADMIN_EMAIL', 'admin@example.com')),
]
MANAGERS = ADMINS

# パフォーマンス設定
CONN_MAX_AGE = 60  # データベース接続持続時間

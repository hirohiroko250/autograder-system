with open('settings_production.py', 'r') as f:
    content = f.read()

# Temporarily use SQLite for export
content = content.replace(
    '''if os.environ.get('DATABASE_URL'):
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
    }''',
    '''# Temporarily use SQLite for export
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db_production.sqlite3',
    }
}'''
)

with open('settings_production.py', 'w') as f:
    f.write(content)
print('Switched to SQLite for export')

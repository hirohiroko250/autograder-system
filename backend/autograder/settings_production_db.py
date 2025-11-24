import os
import dj_database_url

# PostgreSQL使用
if os.environ.get('DATABASE_URL'):
    DATABASES = {
        'default': dj_database_url.parse(os.environ.get('DATABASE_URL'))
    }
else:
    # デフォルトでPostgreSQL
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'autograder_db',
            'USER': 'autograder_user',
            'PASSWORD': 'autograder_password_2025',
            'HOST': 'db',
            'PORT': '5432',
        }
    }

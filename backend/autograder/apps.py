from django.apps import AppConfig


class AutograderConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'autograder'
    verbose_name = '管理設定'
    
    def ready(self):
        # admin設定をインポート
        from . import admin
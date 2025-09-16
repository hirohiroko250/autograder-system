from django.apps import AppConfig

class TestSchedulesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'test_schedules'
    verbose_name = 'テスト日程'

    def ready(self):
        import test_schedules.signals
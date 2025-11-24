from django.db import models
from django.core.validators import RegexValidator

class TestScheduleInfo(models.Model):
    PERIOD_CHOICES = [
        ('spring', '春期'),
        ('summer', '夏期'),
        ('winter', '冬期'),
    ]
    
    STATUS_CHOICES = [
        ('scheduled', '予定'),
        ('in_progress', '実施中'),
        ('completed', '完了'),
    ]
    
    year = models.CharField(
        max_length=4,
        validators=[RegexValidator(r'^\d{4}$', '4桁の年を入力してください')],
        verbose_name='年度'
    )
    period = models.CharField(
        max_length=10,
        choices=PERIOD_CHOICES,
        verbose_name='期間'
    )
    planned_date = models.DateField(verbose_name='予定日')
    actual_date = models.DateField(null=True, blank=True, verbose_name='実施日')
    deadline = models.DateTimeField(verbose_name='締切日時')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='scheduled',
        verbose_name='ステータス'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='作成日時')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新日時')
    
    class Meta:
        db_table = 'test_schedule_info'
        verbose_name = 'テスト日程情報'
        verbose_name_plural = 'テスト日程情報'
        unique_together = ['year', 'period']
        indexes = [
            models.Index(fields=['year', 'period']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.year}年度 {self.get_period_display()}"
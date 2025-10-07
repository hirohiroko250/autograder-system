from django.db import models
from .models import Student

class StudentEnrollment(models.Model):
    PERIOD_CHOICES = [
        ('spring', '春期'),
        ('summer', '夏期'),
        ('winter', '冬期'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='enrollments', verbose_name='生徒')
    year = models.IntegerField(verbose_name='年度')
    period = models.CharField(max_length=10, choices=PERIOD_CHOICES, verbose_name='学期')
    is_active = models.BooleanField(default=True, verbose_name='アクティブ')
    enrolled_at = models.DateTimeField(auto_now_add=True, verbose_name='受講開始日')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='作成日時')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新日時')
    
    class Meta:
        db_table = 'student_enrollments'
        verbose_name = '生徒受講情報'
        verbose_name_plural = '生徒受講情報'
        unique_together = ['student', 'year', 'period']
        indexes = [
            models.Index(fields=['year', 'period']),
            models.Index(fields=['student', 'year', 'period']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.student.name} - {self.year}年度 {self.get_period_display()}"
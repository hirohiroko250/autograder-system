from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Notification(models.Model):
    """システム通知モデル"""
    NOTIFICATION_TYPES = [
        ('test_created', 'テスト追加'),
        ('test_updated', 'テスト更新'),
        ('deadline_reminder', '締切リマインダー'),
        ('system', 'システム通知'),
    ]

    title = models.CharField(max_length=255, verbose_name='タイトル')
    message = models.TextField(verbose_name='メッセージ')
    notification_type = models.CharField(
        max_length=20, 
        choices=NOTIFICATION_TYPES, 
        default='system',
        verbose_name='通知種別'
    )
    is_read = models.BooleanField(default=False, verbose_name='既読')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='作成日時')
    
    # 関連情報（オプション）
    test_id = models.IntegerField(null=True, blank=True, verbose_name='関連テストID')
    year = models.IntegerField(null=True, blank=True, verbose_name='関連年度')
    period = models.CharField(max_length=10, null=True, blank=True, verbose_name='関連時期')

    class Meta:
        db_table = 'notifications'
        verbose_name = '通知'
        verbose_name_plural = '通知'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['notification_type']),
            models.Index(fields=['is_read']),
        ]

    def __str__(self):
        return f"{self.title} ({self.get_notification_type_display()})"


class UserNotification(models.Model):
    """ユーザー別通知モデル"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='ユーザー')
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE, verbose_name='通知')
    is_read = models.BooleanField(default=False, verbose_name='既読')
    read_at = models.DateTimeField(null=True, blank=True, verbose_name='既読日時')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='作成日時')

    class Meta:
        db_table = 'user_notifications'
        verbose_name = 'ユーザー通知'
        verbose_name_plural = 'ユーザー通知'
        unique_together = ['user', 'notification']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['created_at']),
        ]

    def mark_as_read(self):
        """通知を既読にする"""
        from django.utils import timezone
        self.is_read = True
        self.read_at = timezone.now()
        self.save(update_fields=['is_read', 'read_at'])

    def __str__(self):
        return f"{self.user.username} - {self.notification.title}"
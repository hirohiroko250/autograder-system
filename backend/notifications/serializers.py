from rest_framework import serializers
from .models import Notification, UserNotification


class NotificationSerializer(serializers.ModelSerializer):
    notification_type_display = serializers.CharField(source='get_notification_type_display', read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id', 'title', 'message', 'notification_type', 'notification_type_display',
            'is_read', 'created_at', 'test_id', 'year', 'period'
        ]
        read_only_fields = ['id', 'created_at']


class UserNotificationSerializer(serializers.ModelSerializer):
    notification = NotificationSerializer(read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)

    class Meta:
        model = UserNotification
        fields = [
            'id', 'user', 'user_name', 'notification', 'is_read', 'read_at', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'created_at']


class UserNotificationListSerializer(serializers.ModelSerializer):
    """ユーザー向け通知リスト用のシンプルなシリアライザー"""
    title = serializers.CharField(source='notification.title')
    message = serializers.CharField(source='notification.message')
    notification_type = serializers.CharField(source='notification.notification_type')
    notification_type_display = serializers.CharField(source='notification.get_notification_type_display')
    test_id = serializers.IntegerField(source='notification.test_id')
    year = serializers.IntegerField(source='notification.year')
    period = serializers.CharField(source='notification.period')

    class Meta:
        model = UserNotification
        fields = [
            'id', 'title', 'message', 'notification_type', 'notification_type_display',
            'is_read', 'read_at', 'created_at', 'test_id', 'year', 'period'
        ]
        read_only_fields = ['id', 'created_at']
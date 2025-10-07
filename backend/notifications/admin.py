from django.contrib import admin
from .models import Notification, UserNotification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'notification_type', 'year', 'period', 'created_at', 'is_read']
    list_filter = ['notification_type', 'year', 'period', 'is_read', 'created_at']
    search_fields = ['title', 'message']
    readonly_fields = ['created_at']
    
    fieldsets = (
        (None, {
            'fields': ('title', 'message', 'notification_type', 'is_read')
        }),
        ('関連情報', {
            'fields': ('test_id', 'year', 'period'),
            'classes': ('collapse',)
        }),
        ('メタ情報', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(UserNotification)
class UserNotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'notification', 'is_read', 'read_at', 'created_at']
    list_filter = ['is_read', 'created_at', 'notification__notification_type']
    search_fields = ['user__username', 'notification__title']
    readonly_fields = ['created_at', 'read_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'notification')
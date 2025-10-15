from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from .models import Notification, UserNotification
from .serializers import (
    NotificationSerializer, 
    UserNotificationSerializer, 
    UserNotificationListSerializer
)

User = get_user_model()


class NotificationViewSet(viewsets.ModelViewSet):
    """システム通知管理用ViewSet（管理者のみ）"""
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        """管理者のみ作成・更新・削除可能"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        
        return [permission() for permission in permission_classes]


class UserNotificationViewSet(viewsets.ModelViewSet):
    """ユーザー通知管理用ViewSet"""
    serializer_class = UserNotificationListSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """ログインユーザーの通知のみを取得"""
        return UserNotification.objects.filter(
            user=self.request.user
        ).select_related('notification').order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """通知を既読にする"""
        try:
            user_notification = self.get_object()
            user_notification.mark_as_read()
            
            return Response({
                'success': True,
                'message': '通知を既読にしました'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        """すべての未読通知を既読にする"""
        try:
            unread_notifications = self.get_queryset().filter(is_read=False)
            count = 0
            
            for notification in unread_notifications:
                notification.mark_as_read()
                count += 1
            
            return Response({
                'success': True,
                'message': f'{count}件の通知を既読にしました',
                'count': count
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """未読通知数を取得"""
        try:
            count = self.get_queryset().filter(is_read=False).count()
            
            return Response({
                'success': True,
                'unread_count': count
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
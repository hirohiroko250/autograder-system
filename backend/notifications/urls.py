from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NotificationViewSet, UserNotificationViewSet

router = DefaultRouter()
router.register(r'notifications', NotificationViewSet)
router.register(r'user-notifications', UserNotificationViewSet, basename='user-notifications')

urlpatterns = [
    path('', include(router.urls)),
]
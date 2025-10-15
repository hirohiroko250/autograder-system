from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'schedules', views.TestScheduleViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('<int:year>/<str:period>/files/', views.TestFileListView.as_view(), name='test-files-list'),
    path('<int:year>/<str:period>/files/<str:file_id>/download/', views.TestFileDownloadView.as_view(), name='test-file-download'),
    path('<int:year>/<str:period>/files/bulk-download/', views.TestFileBulkDownloadView.as_view(), name='test-files-bulk-download'),
]
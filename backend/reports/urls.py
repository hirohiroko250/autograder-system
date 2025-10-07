from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    # テスト結果帳票生成
    path('test-report/', views.test_report_generator_view, name='test_report_generator'),
    
    # レポートデータのプレビュー（AJAX API）
    path('api/preview/', views.preview_report_data, name='preview_report_data'),
    
    # 一括帳票生成
    path('bulk-report/', views.bulk_report_generation_view, name='bulk_report_generation'),
]
from django.urls import path
from . import views
from scores.report_views import preview_individual_report, preview_bulk_reports

app_name = 'reports'

urlpatterns = [
    # テスト結果帳票生成
    path('test-report/', views.test_report_generator_view, name='test_report_generator'),

    # レポートデータのプレビュー（AJAX API）
    path('api/preview/', views.preview_report_data, name='preview_report_data'),

    # 一括帳票生成
    path('bulk-report/', views.bulk_report_generation_view, name='bulk_report_generation'),

    # HTML帳票プレビュー（認証不要）
    path('preview/', preview_individual_report, name='preview_individual_report'),
    path('preview-bulk/', preview_bulk_reports, name='preview_bulk_reports'),
]
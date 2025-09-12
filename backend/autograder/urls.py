from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.http import HttpResponse
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from schools.views import SchoolViewSet
from students.views import StudentViewSet, StudentEnrollmentViewSet
from scores.views import (
    ScoreViewSet, TestResultViewSet, CommentTemplateViewSet, CommentTemplateV2ViewSet,
    StudentCommentViewSet, TestCommentViewSet, 
    QuestionScoreViewSet, TestAttendanceViewSet,
    IndividualProblemViewSet, IndividualProblemScoreViewSet, import_csv_scores
)
from notifications.views import NotificationViewSet, UserNotificationViewSet
from tests.views import TestScheduleViewSet, TestDefinitionViewSet, QuestionGroupViewSet, QuestionViewSet
from classrooms.views import ClassroomViewSet
from test_schedules.views import TestScheduleInfoViewSet
from schools.utils import export_school_template
import io
import pandas as pd

def redirect_to_frontend(request):
    """管理画面の「サイトを表示」ボタンで塾ページにリダイレクト"""
    return redirect('http://localhost:3000')

def download_school_template(request):
    """塾登録テンプレートを直接ダウンロード"""
    df = export_school_template()
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='塾登録テンプレート')
    
    output.seek(0)
    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="school_template.xlsx"'
    return response

# DRF Router
router = DefaultRouter()
router.register(r'schools', SchoolViewSet, basename='school')
router.register(r'students', StudentViewSet, basename='student')
router.register(r'student-enrollments', StudentEnrollmentViewSet, basename='studentenrollment')
router.register(r'test-results', TestResultViewSet, basename='testresult')
router.register(r'comment-templates', CommentTemplateViewSet, basename='commenttemplate')
router.register(r'comment-templates-v2', CommentTemplateV2ViewSet, basename='commenttemplatev2')
router.register(r'student-comments', StudentCommentViewSet, basename='studentcomment')
router.register(r'test-comments', TestCommentViewSet, basename='testcomment')
router.register(r'test-schedules', TestScheduleViewSet, basename='testschedule')
router.register(r'test-schedules-info', TestScheduleInfoViewSet, basename='testschedule-info')
router.register(r'tests', TestDefinitionViewSet, basename='testdefinition')
router.register(r'question-groups', QuestionGroupViewSet, basename='questiongroup')
router.register(r'questions', QuestionViewSet, basename='question')
router.register(r'question-scores', QuestionScoreViewSet, basename='questionscore')
router.register(r'test-attendances', TestAttendanceViewSet, basename='testattendance')
router.register(r'individual-problems', IndividualProblemViewSet, basename='individualproblem')
router.register(r'individual-problem-scores', IndividualProblemScoreViewSet, basename='individualproblemscore')
router.register(r'scores', ScoreViewSet, basename='score')
router.register(r'classrooms', ClassroomViewSet, basename='classroom')
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'user-notifications', UserNotificationViewSet, basename='user-notifications')

def csv_import_launcher(request):
    """CSVインポートのランチャーページ"""
    from django.shortcuts import render
    return render(request, 'admin/csv_import_launcher.html')

# テスト結果集計機能は削除されました

urlpatterns = [
    path('admin/scores/csv-import-launcher/', csv_import_launcher, name='csv_import_launcher'),
    path('admin/scores/import-csv/', import_csv_scores, name='admin_import_csv_scores'),
    path('admin/', admin.site.urls),
    path('api/auth/', include('accounts.urls')),
    path('api/', include(router.urls)),
    path('api/tests/', include('tests.urls')),
    path('reports/', include('reports.urls')),
    path('download-school-template/', download_school_template, name='download_school_template'),
    path('admin/schools/import/', include('schools.urls')),
    path('', redirect_to_frontend),  # ルートページで塾ページにリダイレクト
]

# メディアファイルの配信設定（開発環境用）
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
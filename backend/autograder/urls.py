from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.http import HttpResponse
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.admin.views.decorators import staff_member_required
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
    return redirect('http://172.20.10.2:3000')

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

def bulk_add_school_billing(request):
    """課金レポート一括追加ページ"""
    from django.shortcuts import render, redirect
    from django.contrib import messages
    from django.contrib.admin.views.decorators import staff_member_required
    from classrooms.utils import generate_school_billing_report
    from schools.models import School
    from datetime import datetime

    if request.method == 'POST':
        year = request.POST.get('year')
        period = request.POST.get('period')
        overwrite = bool(request.POST.get('overwrite'))

        if not year or not period:
            messages.error(request, '年度と期間を選択してください。')
        else:
            try:
                year = int(year)
                schools = School.objects.all()
                created_count = 0
                updated_count = 0
                skipped_count = 0
                error_count = 0

                for school in schools:
                    try:
                        result = generate_school_billing_report(school, year, period, force=overwrite)

                        if result.get('created'):
                            created_count += 1
                        elif result.get('updated'):
                            updated_count += 1
                        else:
                            skipped_count += 1
                    except Exception as e:
                        error_count += 1
                        messages.warning(request, f'{school.name}: {str(e)}')

                if created_count:
                    messages.success(request, f'{created_count}件の塾別課金レポートを新規生成しました。（{year}年度 {period}期）')
                if updated_count:
                    messages.success(request, f'{updated_count}件の塾別課金レポートを再計算しました。')
                if skipped_count and not overwrite:
                    messages.info(request, f'{skipped_count}件は既存レポートがあるためスキップしました。再計算する場合は「上書きして再生成」を有効にしてください。')
                if error_count > 0:
                    messages.warning(request, f'{error_count}個の塾でエラーが発生しました。')

            except ValueError:
                messages.error(request, '有効な年度を入力してください。')
            except Exception as e:
                messages.error(request, f'処理中にエラーが発生しました: {str(e)}')

        return redirect('admin:classrooms_schoolbillingreport_changelist')

    # GET リクエストの場合、フォームを表示
    current_year = datetime.now().year
    years = list(range(current_year - 2, current_year + 3))  # 前後2年の範囲
    periods = [
        ('spring', '春期'),
        ('summer', '夏期'),
        ('winter', '冬期'),
    ]

    context = {
        'title': '課金レポート一括追加',
        'years': years,
        'periods': periods,
        'overwrite': False,
    }
    return render(request, 'admin/bulk_add_billing.html', context)

bulk_add_school_billing = staff_member_required(bulk_add_school_billing)

# テスト結果集計機能は削除されました

def redirect_billing_to_school_billing(request, **kwargs):
    """教室ベース課金レポートへのアクセスを塾ベース課金レポートにリダイレクト"""
    from django.shortcuts import redirect
    from django.contrib import messages

    # add/ が含まれている場合は一括追加ページに、そうでなければリストページに
    if 'add' in request.path:
        messages.info(request, '課金レポートは一括追加機能をご利用ください。')
        return redirect('bulk_add_school_billing')
    else:
        messages.info(request, '課金レポートは塾ベースの管理に統一されました。')
        return redirect('admin:classrooms_schoolbillingreport_changelist')

# 教室ベース課金レポートへのアクセスを強制的に塾ベースにリダイレクト（admin URLより優先）
billing_redirect_patterns = [
    path('admin/classrooms/billingreport/', redirect_billing_to_school_billing, name='billing_redirect_list'),
    path('admin/classrooms/billingreport/add/', redirect_billing_to_school_billing, name='billing_redirect_add'),
    path('admin/classrooms/billingreport/<int:id>/', redirect_billing_to_school_billing, name='billing_redirect_detail'),
    path('admin/classrooms/billingreport/<int:id>/change/', redirect_billing_to_school_billing, name='billing_redirect_change'),
    path('admin/classrooms/billingreport/<int:id>/delete/', redirect_billing_to_school_billing, name='billing_redirect_delete'),
]

urlpatterns = billing_redirect_patterns + [
    path('admin/scores/csv-import-launcher/', csv_import_launcher, name='csv_import_launcher'),
    path('admin/scores/import-csv/', import_csv_scores, name='admin_import_csv_scores'),
    path('admin/bulk-add-school-billing/', bulk_add_school_billing, name='bulk_add_school_billing'),
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
    from .media_views import secure_media_serve
    from django.urls import re_path
    # カスタムメディアファイル配信（エラーハンドリング付き）
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', secure_media_serve, name='secure_media'),
    ]

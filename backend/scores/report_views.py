"""
個人成績表プレビュー用のスタンドアロンビュー
認証なしでアクセス可能
"""
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.conf import settings
from .utils import get_individual_report_data
import os
from datetime import datetime


def preview_individual_report(request):
    """個別成績表HTML印刷プレビュー（認証不要）"""
    student_id = request.GET.get('studentId')
    year = request.GET.get('year')
    period = request.GET.get('period')

    if not all([student_id, year, period]):
        return HttpResponse(
            '<html><body><h1>エラー</h1><p>studentId, year, periodパラメータが必要です</p></body></html>',
            content_type='text/html'
        )

    # 成績データを取得
    report_data = get_individual_report_data(student_id, year, period)
    if not report_data:
        return HttpResponse(
            '<html><body><h1>エラー</h1><p>該当する成績データが見つかりません</p></body></html>',
            content_type='text/html'
        )

    # CSS読み込み
    css_path = os.path.join(settings.BASE_DIR, 'static', 'reports', 'report.css')
    try:
        with open(css_path, 'r', encoding='utf-8') as f:
            css_content = f.read()
    except FileNotFoundError:
        css_content = ''

    # ロゴパス
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'reports', 'logo.svg')

    # テンプレートデータ準備
    template_data = {
        'css_content': css_content,
        'logo_url': f'file://{logo_path}',
        'issue_date': datetime.now().strftime('%Y年%m月%d日'),
        **report_data
    }

    # HTML生成
    html_content = render_to_string('reports/individual_report.html', template_data)

    # 印刷用のJavaScriptを追加
    print_script = '''
<script>
function printReport() {
    window.print();
}

// Ctrl+P または Cmd+P でも印刷可能
document.addEventListener('keydown', function(e) {
    if ((e.ctrlKey || e.metaKey) && e.key === 'p') {
        e.preventDefault();
        window.print();
    }
});

// ページロード時に印刷ダイアログを表示
window.addEventListener('load', function() {
    setTimeout(function() {
        window.print();
    }, 500);
});
</script>
</body>
</html>'''

    # HTMLの最後に印刷スクリプトを挿入
    html_content = html_content.replace('</body>\n</html>', print_script)

    return HttpResponse(html_content, content_type='text/html; charset=utf-8')


def preview_bulk_reports(request):
    """一括成績表HTML印刷プレビュー（認証不要）"""
    year = request.GET.get('year')
    period = request.GET.get('period')
    classroom_id = request.GET.get('classroomId')
    student_ids = request.GET.get('studentIds', '')

    if not all([year, period]):
        return HttpResponse(
            '<html><body><h1>エラー</h1><p>year, periodパラメータが必要です</p></body></html>',
            content_type='text/html'
        )

    # 学生ID配列を解析
    if student_ids:
        student_id_list = [s.strip() for s in student_ids.split(',') if s.strip()]
    else:
        student_id_list = []

    if not student_id_list:
        return HttpResponse(
            '<html><body><h1>エラー</h1><p>studentIdsパラメータが必要です</p></body></html>',
            content_type='text/html'
        )

    # CSS読み込み
    css_path = os.path.join(settings.BASE_DIR, 'static', 'reports', 'report.css')
    try:
        with open(css_path, 'r', encoding='utf-8') as f:
            css_content = f.read()
    except FileNotFoundError:
        css_content = ''

    # ロゴパス
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'reports', 'logo.svg')

    # 複数の成績表を生成
    html_pages = []
    for student_id in student_id_list:
        report_data = get_individual_report_data(student_id, year, period)
        if report_data:
            template_data = {
                'css_content': css_content,
                'logo_url': f'file://{logo_path}',
                'issue_date': datetime.now().strftime('%Y年%m月%日'),
                **report_data
            }
            html_page = render_to_string('reports/individual_report.html', template_data)
            html_pages.append(html_page)

    if not html_pages:
        return HttpResponse(
            '<html><body><h1>エラー</h1><p>該当する成績データが見つかりません</p></body></html>',
            content_type='text/html'
        )

    # 複数ページを結合（改ページ付き）
    combined_html = '\n'.join(html_pages)

    # 印刷用のJavaScriptを追加
    print_script = '''
<script>
function printReport() {
    window.print();
}

// Ctrl+P または Cmd+P でも印刷可能
document.addEventListener('keydown', function(e) {
    if ((e.ctrlKey || e.metaKey) && e.key === 'p') {
        e.preventDefault();
        window.print();
    }
});

// ページロード時に印刷ダイアログを表示
window.addEventListener('load', function() {
    setTimeout(function() {
        window.print();
    }, 500);
});
</script>
</body>
</html>'''

    # HTMLの最後に印刷スクリプトを挿入
    combined_html = combined_html.replace('</body>\n</html>', print_script)

    return HttpResponse(combined_html, content_type='text/html; charset=utf-8')

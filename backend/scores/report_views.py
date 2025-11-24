"""
個人成績表プレビュー用のスタンドアロンビュー
認証なしでアクセス可能
"""
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.conf import settings
from .utils import _collect_individual_report_data, _prepare_template_data
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
    report_data, error = _collect_individual_report_data(student_id, int(year), period)
    if error or not report_data:
        return HttpResponse(
            f'<html><body><h1>エラー</h1><p>{error or "該当する成績データが見つかりません"}</p></body></html>',
            content_type='text/html'
        )

    # ロゴパス
    logo_svg = os.path.join(settings.BASE_DIR, 'static', 'reports', 'logo.svg')
    logo_png = os.path.join(settings.BASE_DIR, 'static', 'reports', 'logo.png')
    logo_path = logo_svg if os.path.exists(logo_svg) else logo_png

    # テンプレートデータ準備（SVGグラフを含む）
    template_data = _prepare_template_data(report_data, logo_path)

    # HTML生成
    html_content = render_to_string('reports/individual_report.html', template_data)

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

    # ロゴパス
    logo_svg = os.path.join(settings.BASE_DIR, 'static', 'reports', 'logo.svg')
    logo_png = os.path.join(settings.BASE_DIR, 'static', 'reports', 'logo.png')
    logo_path = logo_svg if os.path.exists(logo_svg) else logo_png

    # 複数の成績表を生成
    html_pages = []
    for student_id in student_id_list:
        report_data, error = _collect_individual_report_data(student_id, int(year), period)
        if report_data and not error:
            # テンプレートデータ準備（SVGグラフを含む）
            template_data = _prepare_template_data(report_data, logo_path)
            html_page = render_to_string('reports/individual_report.html', template_data)
            html_pages.append(html_page)

    if not html_pages:
        return HttpResponse(
            '<html><body><h1>エラー</h1><p>該当する成績データが見つかりません</p></body></html>',
            content_type='text/html'
        )

    # 複数ページを結合
    combined_html = ''
    
    # 印刷ボタンとスタイルを追加
    combined_html += '''
<style>
@media print {
    .print-button {
        display: none !important;
    }
    .page-break {
        page-break-after: always;
    }
}
.print-button {
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 9999;
    padding: 10px 20px;
    background-color: #3498db;
    color: white;
    border: none;
    border-radius: 5px;
    cursor: pointer;
    font-weight: bold;
    box-shadow: 0 2px 5px rgba(0,0,0,0.2);
}
.print-button:hover {
    background-color: #2980b9;
}
</style>
<button class="print-button" onclick="window.print()">🖨️ 印刷 / PDF保存 (全''' + str(len(html_pages)) + '''枚)</button>
'''

    css_content = ''
    if html_pages:
        # 最初のページの<head>部分からCSSを抽出
        import re
        head_match = re.search(r'<head>(.*?)</head>', html_pages[0], re.DOTALL)
        if head_match:
            # <meta charset="utf-8">は後で追加するので除外
            css_content = re.sub(r'<meta charset="utf-8">', '', head_match.group(1), flags=re.IGNORECASE)

    for i, page in enumerate(html_pages):
        # <html>, <head>, <body>タグを除去してコンテンツのみ抽出
        import re
        body_content = re.search(r'<body>(.*?)</body>', page, re.DOTALL)
        if body_content:
            content = body_content.group(1)
            # 最後のページ以外は改ページを追加
            if i < len(html_pages) - 1:
                content += '<div class="page-break"></div>'
            combined_html += content

    combined_html = f'<html><head><meta charset="utf-8">{css_content}</head><body>{combined_html}</body></html>'

    return HttpResponse(combined_html, content_type='text/html; charset=utf-8')

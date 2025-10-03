"""
個人成績表PDF生成（デザイン仕様準拠版）
全国学力向上テスト帳票デザイン.pdfに基づいた実装
"""
import os
from datetime import datetime
from typing import Optional, Tuple
from django.conf import settings

# グローバル変数
PDF_FONTS_REGISTERED = False

def _register_japanese_fonts():
    """日本語フォントを登録"""
    global PDF_FONTS_REGISTERED
    if PDF_FONTS_REGISTERED:
        return

    try:
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont

        # IPAフォント（オープンソース）を使用
        # これらは文字化けしない
        font_path = os.path.join(settings.BASE_DIR, 'static', 'fonts')

        # フォールバック: 利用可能なシステムフォントを試す
        try:
            # Linux/Dockerコンテナでよく利用可能なフォント
            pdfmetrics.registerFont(TTFont('Japanese', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
        except:
            try:
                # 別のフォールバック
                from reportlab.pdfbase.cidfonts import UnicodeCIDFont
                pdfmetrics.registerFont(UnicodeCIDFont('HeiseiKakuGo-W5'))
            except:
                pass  # フォント登録失敗は後でハンドル

        PDF_FONTS_REGISTERED = True
    except Exception as e:
        print(f"フォント登録エラー: {e}")

def create_individual_report_pdf_v2(report_data: dict) -> Tuple[Optional[str], Optional[str]]:
    """
    個人成績表PDFを生成（デザイン仕様準拠版）

    Args:
        report_data: 成績データ

    Returns:
        (file_path, error_message) のタプル
    """
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.units import mm
        from reportlab.platypus import Table, TableStyle
    except ImportError as exc:
        return None, f'PDF生成に必要なライブラリが不足しています: {exc}'

    _register_japanese_fonts()

    # 出力先ディレクトリ
    reports_dir = os.path.join(settings.MEDIA_ROOT, 'reports')
    os.makedirs(reports_dir, exist_ok=True)

    # ファイル名
    file_name = f"individual_report_{report_data['student_info']['id']}_{report_data['test_info']['year']}_{report_data['test_info']['period']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    file_path = os.path.join(reports_dir, file_name)

    # A4サイズ（縦）
    c = canvas.Canvas(file_path, pagesize=A4)
    width, height = A4

    # 色定義（デザイン仕様準拠）
    COLOR_MATH = colors.HexColor('#00A650')  # 算数: 緑
    COLOR_JAPANESE = colors.HexColor('#FF8C00')  # 国語: オレンジ
    COLOR_TOTAL = colors.HexColor('#00A0E9')  # 合計: 水色
    COLOR_HEADER_BG = colors.HexColor('#F0F0F0')

    # フォント設定
    try:
        font_name = 'Japanese'
        c.setFont(font_name, 10)
    except:
        font_name = 'Helvetica'  # フォールバック

    # ===== ヘッダー部分 =====
    y = height - 30*mm

    # タイトル
    c.setFont(font_name, 20)
    c.drawString(30*mm, y, '全国学力向上テスト  個人成績表')

    # 発行日
    c.setFont(font_name, 10)
    c.drawRightString(width - 20*mm, y, f'発行日：{datetime.now().strftime("%Y年%m月%d日")}')

    y -= 15*mm

    # 年度・回・学年情報
    test_info = report_data['test_info']
    student_info = report_data['student_info']

    info_text = f"{test_info['year']}年度  第{test_info.get('iteration', '1')}回  学年 {student_info['grade']}"
    c.setFont(font_name, 12)
    c.drawString(30*mm, y, info_text)

    y -= 10*mm

    # 生徒情報テーブル
    student_data = [
        ['塾ID', student_info.get('school_id', ''), '塾名', student_info.get('school_name', ''),
         '生徒ID', student_info['id'], '受験ID', '', '学年', student_info['grade'], '生徒氏名', student_info['name']]
    ]

    student_table = Table(student_data, colWidths=[15*mm, 20*mm, 15*mm, 30*mm, 15*mm, 20*mm, 15*mm, 20*mm, 15*mm, 15*mm, 20*mm, 30*mm])
    student_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), font_name),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BACKGROUND', (0, 0), (0, 0), COLOR_HEADER_BG),
        ('BACKGROUND', (2, 0), (2, 0), COLOR_HEADER_BG),
        ('BACKGROUND', (4, 0), (4, 0), COLOR_HEADER_BG),
        ('BACKGROUND', (6, 0), (6, 0), COLOR_HEADER_BG),
        ('BACKGROUND', (8, 0), (8, 0), COLOR_HEADER_BG),
        ('BACKGROUND', (10, 0), (10, 0), COLOR_HEADER_BG),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))

    student_table.wrapOn(c, width, height)
    student_table.drawOn(c, 20*mm, y - 15*mm)

    y -= 30*mm

    # ===== 左側: 得点・偏差値・順位 =====
    subjects = report_data.get('subjects', {})
    subject_order = report_data.get('subject_order', ['math', 'japanese'])
    combined = report_data.get('combined', {})

    # 得点テーブルのヘッダー
    score_headers = [['教科', '算数', '国語', '合計']]

    # 各行のデータ
    score_data = [
        ['得点',
         f"{subjects.get('math', {}).get('total_score', 0)}点",
         f"{subjects.get('japanese', {}).get('total_score', 0)}点",
         f"{combined.get('total_score', 0)}点"],
        ['偏差値',
         f"{subjects.get('math', {}).get('deviation', 0):.1f}",
         f"{subjects.get('japanese', {}).get('deviation', 0):.1f}",
         f"{combined.get('deviation', 0):.1f}"],
        ['全国順位（受験者数）',
         f"{subjects.get('math', {}).get('rankings', {}).get('national', {}).get('rank', 0)}位({subjects.get('math', {}).get('rankings', {}).get('national', {}).get('total', 0)}人中)",
         f"{subjects.get('japanese', {}).get('rankings', {}).get('national', {}).get('rank', 0)}位({subjects.get('japanese', {}).get('rankings', {}).get('national', {}).get('total', 0)}人中)",
         f"{combined.get('rankings', {}).get('national', {}).get('rank', 0)}位({combined.get('rankings', {}).get('national', {}).get('total', 0)}人中)"],
        ['塾内順位（受験者数）',
         f"{subjects.get('math', {}).get('rankings', {}).get('school', {}).get('rank', 0)}位({subjects.get('math', {}).get('rankings', {}).get('school', {}).get('total', 0)}人中)",
         f"{subjects.get('japanese', {}).get('rankings', {}).get('school', {}).get('rank', 0)}位({subjects.get('japanese', {}).get('rankings', {}).get('school', {}).get('total', 0)}人中)",
         f"{combined.get('rankings', {}).get('school', {}).get('rank', 0)}位({combined.get('rankings', {}).get('school', {}).get('total', 0)}人中)"],
        ['最高点（全国）',
         f"{subjects.get('math', {}).get('statistics', {}).get('national_highest', 0)}点",
         f"{subjects.get('japanese', {}).get('statistics', {}).get('national_highest', 0)}点",
         f"{combined.get('statistics', {}).get('national_highest', 0)}点"],
        ['最高点（塾内）',
         f"{subjects.get('math', {}).get('statistics', {}).get('school_highest', 0)}点",
         f"{subjects.get('japanese', {}).get('statistics', {}).get('school_highest', 0)}点",
         f"{combined.get('statistics', {}).get('school_highest', 0)}点"],
        ['平均点（全国）',
         f"{subjects.get('math', {}).get('statistics', {}).get('national_average', 0):.1f}点",
         f"{subjects.get('japanese', {}).get('statistics', {}).get('national_average', 0):.1f}点",
         f"{combined.get('averages', {}).get('national', 0):.1f}点"],
        ['平均点（塾内）',
         f"{subjects.get('math', {}).get('statistics', {}).get('school_average', 0):.1f}点",
         f"{subjects.get('japanese', {}).get('statistics', {}).get('school_average', 0):.1f}点",
         f"{combined.get('averages', {}).get('school', 0):.1f}点"],
    ]

    full_score_data = score_headers + score_data

    score_table = Table(full_score_data, colWidths=[40*mm, 30*mm, 30*mm, 30*mm])
    score_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), font_name),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BACKGROUND', (0, 0), (0, 0), COLOR_HEADER_BG),
        ('BACKGROUND', (1, 0), (1, 0), COLOR_MATH),
        ('BACKGROUND', (2, 0), (2, 0), COLOR_JAPANESE),
        ('BACKGROUND', (3, 0), (3, 0), COLOR_TOTAL),
        ('TEXTCOLOR', (1, 0), (3, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (0, -1), font_name),
        ('FONTSIZE', (1, 1), (3, 1), 16),  # 得点を大きく
        ('FONTNAME', (1, 1), (3, 1), font_name),
    ]))

    score_table.wrapOn(c, width, height)
    score_table.drawOn(c, 20*mm, y - 80*mm)

    # ===== PDFを保存 =====
    c.save()

    try:
        os.chmod(file_path, 0o644)
    except OSError:
        pass

    return file_path, None

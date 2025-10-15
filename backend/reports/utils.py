import pandas as pd
import io
from datetime import datetime
from django.db.models import Q, Avg, Count
from django.http import HttpResponse

# PDF関連のインポートをtry-catchで囲む
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    PDF_AVAILABLE = True
except ImportError as e:
    print(f"Warning: PDF generation unavailable - {e}")
    PDF_AVAILABLE = False

from scores.models import Score, TestResult
from students.models import Student
from tests.models import TestDefinition
from classrooms.models import Classroom


class TestReportGenerator:
    """テスト結果帳票生成クラス"""
    
    def __init__(self, year, period, subject=None, grade_level=None):
        self.year = year
        self.period = period
        self.subject = subject
        self.grade_level = grade_level
        self.period_display = {
            'spring': '春期',
            'summer': '夏期', 
            'winter': '冬期'
        }.get(period, period)
    
    def get_test_results_data(self, school_id=None, classroom_id=None):
        """テスト結果データを取得"""
        
        # テスト結果の基本クエリ（関連データを効率的に一括取得）
        queryset = TestResult.objects.select_related(
            'student', 'test', 'student__classroom', 'student__classroom__school'
        ).prefetch_related(
            'student__score_set__question_group'
        ).filter(
            test__schedule__year=self.year,
            test__schedule__period=self.period
        )
        
        # フィルタリング条件を適用
        if self.subject:
            queryset = queryset.filter(test__subject=self.subject)
        
        if self.grade_level:
            queryset = queryset.filter(test__grade_level=self.grade_level)
        
        if school_id:
            queryset = queryset.filter(student__classroom__school__school_id=school_id)
        
        if classroom_id:
            queryset = queryset.filter(student__classroom__classroom_id=classroom_id)
        
        return queryset.order_by(
            'student__classroom__school__school_id',
            'student__classroom__classroom_id',
            'student__student_id'
        )
    
    def generate_excel_report(self, school_id=None, classroom_id=None):
        """Excel形式のレポートを生成"""
        
        test_results = self.get_test_results_data(school_id, classroom_id)
        
        if not test_results.exists():
            return None, "対象データが見つかりません"
        
        # スコアデータを一括取得してキャッシュ（N+1問題を完全に回避）
        score_cache = {}
        all_scores = Score.objects.filter(
            student__in=test_results.values_list('student', flat=True),
            test__in=test_results.values_list('test', flat=True)
        ).select_related('question_group').values(
            'student_id', 'test_id', 'question_group__group_number', 'score'
        )
        
        for score in all_scores:
            key = (score['student_id'], score['test_id'])
            if key not in score_cache:
                score_cache[key] = {}
            if score['question_group__group_number']:
                score_cache[key][f'大問{score["question_group__group_number"]}'] = score['score']
        
        # データをDataFrameに変換
        data = []
        for result in test_results:
            # キャッシュからスコアデータを取得
            question_scores = score_cache.get((result.student.id, result.test.id), {})
            
            # 基本データ
            row_data = {
                '塾ID': result.student.classroom.school.school_id,
                '塾名': result.student.classroom.school.name,
                '教室ID': result.student.classroom.classroom_id,
                '教室名': result.student.classroom.name,
                '会員種別': result.student.classroom.get_membership_type_display(),
                '料金': f"{result.student.classroom.get_price_per_student()}円",
                '生徒ID': result.student.student_id,
                '生徒名': result.student.name,
                '学年': result.student.grade,
                'テスト': f"{result.test.schedule.year}年度{self.period_display}",
                '科目': result.test.get_subject_display(),
                '合計点': result.total_score,
                '満点': result.test.max_score,
                '正答率': f"{result.correct_rate:.1f}%",
                '塾内順位': result.get_current_school_rank_display(),
                '全国順位': result.get_current_national_rank_display(),
                'コメント': result.comment,
                '更新日時': result.updated_at.strftime('%Y-%m-%d %H:%M'),
            }
            
            # 大問ごとの点数を追加
            row_data.update(question_scores)
            data.append(row_data)
        
        df = pd.DataFrame(data)
        
        # Excelファイルを生成
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # メインデータシート
            df.to_excel(writer, sheet_name='テスト結果一覧', index=False)
            
            # 統計情報シート
            stats_data = self.generate_statistics_data(test_results)
            stats_df = pd.DataFrame(stats_data)
            stats_df.to_excel(writer, sheet_name='統計情報', index=False)
            
            # 塾別集計シート
            school_summary = self.generate_school_summary(test_results)
            school_df = pd.DataFrame(school_summary)
            school_df.to_excel(writer, sheet_name='塾別集計', index=False)
        
        output.seek(0)
        return output, None
    
    def generate_statistics_data(self, test_results):
        """統計情報データを生成"""
        
        if not test_results.exists():
            return []
        
        # 全体統計
        total_students = test_results.count()
        avg_score = test_results.aggregate(avg=Avg('total_score'))['avg'] or 0
        avg_correct_rate = test_results.aggregate(avg=Avg('correct_rate'))['avg'] or 0
        
        # 学年別統計
        grade_stats = test_results.values('student__grade').annotate(
            count=Count('id'),
            avg_score=Avg('total_score'),
            avg_correct_rate=Avg('correct_rate')
        ).order_by('student__grade')
        
        # 塾別統計
        school_stats = test_results.values(
            'student__classroom__school__school_id',
            'student__classroom__school__name'
        ).annotate(
            count=Count('id'),
            avg_score=Avg('total_score'),
            avg_correct_rate=Avg('correct_rate')
        ).order_by('student__classroom__school__school_id')
        
        stats_data = [
            {
                'カテゴリ': '全体',
                '項目': '受験者数',
                '値': total_students
            },
            {
                'カテゴリ': '全体',
                '項目': '平均点',
                '値': f"{avg_score:.1f}点"
            },
            {
                'カテゴリ': '全体',
                '項目': '平均正答率',
                '値': f"{avg_correct_rate:.1f}%"
            }
        ]
        
        # 学年別統計を追加
        for grade_stat in grade_stats:
            stats_data.extend([
                {
                    'カテゴリ': f"学年別-{grade_stat['student__grade']}",
                    '項目': '受験者数',
                    '値': grade_stat['count']
                },
                {
                    'カテゴリ': f"学年別-{grade_stat['student__grade']}",
                    '項目': '平均点',
                    '値': f"{grade_stat['avg_score']:.1f}点"
                },
                {
                    'カテゴリ': f"学年別-{grade_stat['student__grade']}",
                    '項目': '平均正答率',
                    '値': f"{grade_stat['avg_correct_rate']:.1f}%"
                }
            ])
        
        return stats_data
    
    def generate_school_summary(self, test_results):
        """塾別集計データを生成"""
        
        # 塾別基本統計を一括取得
        first_result = test_results.first()
        max_score = first_result.test.max_score if first_result else 0
        
        school_summary = test_results.values(
            'student__classroom__school__school_id',
            'student__classroom__school__name'
        ).annotate(
            total_students=Count('id'),
            avg_score=Avg('total_score'),
            avg_correct_rate=Avg('correct_rate')
        ).order_by('student__classroom__school__school_id')
        
        # 会員種別別集計を一括取得（N+1問題を回避）
        membership_summary = test_results.values(
            'student__classroom__school__school_id',
            'student__classroom__school__membership_type'
        ).annotate(
            count=Count('id')
        )
        
        # 価格マッピング（Schoolモデルの価格設定）
        price_mapping = {
            'culture_kids': 100,
            'eduplus': 300,
            'general': 500,
        }
        
        # 会員種別表示名マッピング
        membership_display_mapping = {
            'culture_kids': 'カルチャーキッズ導入塾',
            'general': '一般塾',
            'eduplus': 'eduplus導入塾',
        }
        
        # 塾ごとの会員種別情報をグルーピング
        school_membership_data = {}
        for item in membership_summary:
            school_id = item['student__classroom__school__school_id']
            membership_type = item['student__classroom__school__membership_type']
            count = item['count']
            
            if school_id not in school_membership_data:
                school_membership_data[school_id] = {}
            
            school_membership_data[school_id][membership_type] = count
        
        summary_data = []
        for summary in school_summary:
            school_id = summary['student__classroom__school__school_id']
            
            # 会員種別内訳を取得
            membership_breakdown = school_membership_data.get(school_id, {})
            
            # 料金計算とディスプレイ情報の生成
            total_fee = 0
            membership_display = []
            
            for membership_type, count in membership_breakdown.items():
                price_per_student = price_mapping.get(membership_type, 500)
                total_fee += count * price_per_student
                
                display_name = membership_display_mapping.get(membership_type, membership_type)
                membership_display.append(f"{display_name}:{count}名({price_per_student}円/名)")
            
            summary_data.append({
                '塾ID': summary['student__classroom__school__school_id'],
                '塾名': summary['student__classroom__school__name'],
                '受験者数': summary['total_students'],
                '平均点': f"{summary['avg_score']:.1f}点",
                '平均正答率': f"{summary['avg_correct_rate']:.1f}%",
                '満点': f"{max_score}点",
                '会員種別内訳': ', '.join(membership_display),
                '合計料金': f"{total_fee:,}円"
            })
        
        return summary_data
    
    def generate_pdf_report(self, school_id=None, classroom_id=None):
        """PDF形式のレポートを生成"""
        
        if not PDF_AVAILABLE:
            return None, "PDF生成機能が利用できません。reportlabライブラリをインストールしてください。"
        
        test_results = self.get_test_results_data(school_id, classroom_id)
        
        if not test_results.exists():
            return None, "対象データが見つかりません"
        
        output = io.BytesIO()
        
        # PDF文書を作成
        doc = SimpleDocTemplate(output, pagesize=A4)
        story = []
        
        # スタイルを設定
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=1  # 中央揃え
        )
        
        # タイトル
        title = f"全国学力向上テスト 結果報告書<br/>{self.year}年度 {self.period_display}"
        if self.subject:
            subject_display = dict(TestDefinition.SUBJECTS).get(self.subject, self.subject)
            title += f" {subject_display}"
        
        story.append(Paragraph(title, title_style))
        story.append(Spacer(1, 20))
        
        # 統計情報を追加
        stats_data = self.generate_statistics_data(test_results)
        if stats_data:
            stats_table_data = [['カテゴリ', '項目', '値']]
            for stat in stats_data:
                stats_table_data.append([
                    stat['カテゴリ'],
                    stat['項目'], 
                    str(stat['値'])
                ])
            
            stats_table = Table(stats_table_data)
            stats_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(Paragraph("統計情報", styles['Heading2']))
            story.append(stats_table)
            story.append(Spacer(1, 20))
        
        # 個人結果テーブル
        story.append(Paragraph("個人別結果", styles['Heading2']))
        
        # テーブルデータを準備
        table_data = [['塾名', '生徒ID', '生徒名', '合計点', '正答率', '塾内順位', '全国順位']]
        
        for result in test_results[:50]:  # PDFは50件まで制限
            table_data.append([
                result.student.classroom.school.name[:10],  # 塾名を短縮
                result.student.student_id,
                result.student.name,
                f"{result.total_score}点",
                f"{result.correct_rate:.1f}%",
                result.get_current_school_rank_display(),
                result.get_current_national_rank_display()
            ])
        
        # テーブルを作成
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(table)
        
        if test_results.count() > 50:
            story.append(Spacer(1, 10))
            story.append(Paragraph(
                f"※ PDF版では上位50件のみ表示しています。全データはExcel版をご利用ください。（全{test_results.count()}件）",
                styles['Normal']
            ))
        
        # PDFを構築
        doc.build(story)
        output.seek(0)
        
        return output, None


def create_excel_response(content, filename):
    """Excel用のHTTPレスポンスを作成"""
    response = HttpResponse(
        content,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def create_pdf_response(content, filename):
    """PDF用のHTTPレスポンスを作成"""
    response = HttpResponse(content, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
#!/usr/bin/env python
"""
グラフデータのデバッグスクリプト
複数の生徒のグラフデータが正しく別々に生成されるか確認する
"""
import os
import sys
import django

# Djangoセットアップ
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'autograder.settings')
django.setup()

from scores.utils import _collect_individual_report_data, _prepare_template_data
from students.models import Student

def debug_graph_data():
    """複数生徒のグラフデータを確認"""
    year = 2025
    period = 'winter'
    
    # テスト対象の生徒を取得（最大5人）
    students = Student.objects.all()[:5]
    
    print(f"\n{'=' * 80}")
    print(f"グラフデータ検証: {year}年 {period}期")
    print(f"{'=' * 80}\n")
    
    for student in students:
        print(f"\n生徒ID: {student.student_id}, 名前: {student.name}, 学年: {student.grade}")
        print("-" * 80)
        
        try:
            # 成績データを収集
            report_data, error = _collect_individual_report_data(student.student_id, year, period)
            
            if error:
                print(f"  エラー: {error}")
                continue
            
            if not report_data:
                print("  データなし")
                continue
            
            # 推移データを確認
            trend_data = report_data.get('trend', {})
            overall_trends = trend_data.get('overall', [])
            subjects_data = trend_data.get('subjects', {})
            math_trends = subjects_data.get('math', [])
            japanese_trends = subjects_data.get('japanese', [])
            
            print(f"  全教科推移データ: {len(overall_trends)}件")
            for i, trend in enumerate(overall_trends[:3]):
                print(f"    {i+1}回: 得点={trend.get('score', 0)}, 平均={trend.get('average', 0):.1f}")
            
            print(f"  算数推移データ: {len(math_trends)}件")
            for i, trend in enumerate(math_trends[:3]):
                print(f"    {i+1}回: 得点={trend.get('score', 0)}, 平均={trend.get('average', 0):.1f}")
            
            print(f"  国語推移データ: {len(japanese_trends)}件")
            for i, trend in enumerate(japanese_trends[:3]):
                print(f"    {i+1}回: 得点={trend.get('score', 0)}, 平均={trend.get('average', 0):.1f}")
            
            # テンプレートデータを準備
            template_data = _prepare_template_data(report_data, '')
            
            # SVGグラフのデータを確認
            total_svg = template_data.get('total_chart_svg', '')
            math_svg = template_data.get('math_chart_svg', '')
            japanese_svg = template_data.get('japanese_chart_svg', '')
            
            print(f"\n  SVGグラフ出力:")
            print(f"    全教科SVG: {len(total_svg)} 文字")
            print(f"    算数SVG: {len(math_svg)} 文字")
            print(f"    国語SVG: {len(japanese_svg)} 文字")
            
            # SVGの中身をチェック（点数表示部分を抽出）
            if '<text' in total_svg:
                import re
                scores = re.findall(r'font-weight="700">(\d+)</text>', total_svg)
                print(f"    全教科グラフの点数表示: {scores}")
            
        except Exception as e:
            import traceback
            print(f"  例外発生: {str(e)}")
            print(traceback.format_exc())
    
    print(f"\n{'=' * 80}\n")

if __name__ == '__main__':
    debug_graph_data()

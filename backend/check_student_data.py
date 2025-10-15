#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'autograder.settings')
django.setup()

from students.models import Student
from scores.models import Score, TestResult
from tests.models import TestSchedule, TestDefinition

# 生徒10574の情報を確認
student_id = '10574'
print(f"=== 生徒 {student_id} の情報確認 ===")

try:
    student = Student.objects.get(student_id=student_id)
    print(f"生徒名: {student.name}")
    print(f"学年: {student.grade}")
    print(f"教室: {student.classroom}")
    print(f"アクティブ: {student.is_active}")
    print()
    
    # テスト結果の確認
    print("=== TestResult テーブル ===")
    test_results = TestResult.objects.filter(student_id=student_id)
    print(f"TestResult件数: {test_results.count()}")
    for result in test_results:
        print(f"  - テストID: {result.test_id}, 総合点: {result.total_score}, 順位: {result.rank}")
    print()
    
    # Scoreテーブルの確認
    print("=== Score テーブル ===")
    scores = Score.objects.filter(student_id=student_id)
    print(f"Score件数: {scores.count()}")
    for score in scores:
        print(f"  - テストID: {score.test_id}, 得点: {score.score}, 出席: {score.attendance}")
    print()
    
    # 利用可能なテストの確認
    print("=== 利用可能なテスト ===")
    test_definitions = TestDefinition.objects.filter(grade_level=student.grade)
    print(f"学年{student.grade}のテスト数: {test_definitions.count()}")
    for test in test_definitions:
        print(f"  - ID: {test.id}, {test.schedule.year}年{test.schedule.get_period_display()}, {test.get_subject_display()}")
    
except Student.DoesNotExist:
    print(f"生徒ID {student_id} が見つかりません")
except Exception as e:
    print(f"エラー: {e}")
#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'autograder.settings')
django.setup()

from tests.models import TestSchedule, TestDefinition
from scores.models import Score, TestResult
from students.models import Student

print("=== テスト定義の確認 ===")
test_definitions = TestDefinition.objects.all()
print(f"総テスト数: {test_definitions.count()}")

for test in test_definitions:
    print(f"ID: {test.id}, {test.schedule.year}年{test.schedule.get_period_display()}, {test.get_subject_display()}, 学年: {test.grade_level}")

print("\n=== スコアデータの確認 ===")
scores = Score.objects.all()
print(f"総スコア数: {scores.count()}")

if scores.count() > 0:
    print("学年別スコア分布:")
    students = Student.objects.all()
    for student in students[:5]:  # 最初の5人だけ表示
        student_scores = scores.filter(student_id=student.student_id).count()
        print(f"  生徒{student.student_id} ({student.grade}年): {student_scores}件")

print("\n=== テスト結果データの確認 ===")
test_results = TestResult.objects.all()
print(f"総テスト結果数: {test_results.count()}")

if test_results.count() > 0:
    print("学年別テスト結果分布:")
    for result in test_results[:5]:  # 最初の5件だけ表示
        try:
            student = Student.objects.get(student_id=result.student_id)
            print(f"  生徒{result.student_id} ({student.grade}年): テストID{result.test_id}, 点数{result.total_score}")
        except Student.DoesNotExist:
            print(f"  生徒{result.student_id}: 生徒情報なし, テストID{result.test_id}, 点数{result.total_score}")
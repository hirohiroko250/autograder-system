#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'autograder.settings')
django.setup()

from students.models import Student
from tests.models import TestDefinition

print("=== 学年マッピング確認 ===")
student_id = '10574'
student = Student.objects.get(student_id=student_id)

print(f"生徒10574の学年: '{student.grade}' (型: {type(student.grade)})")

print("\nテスト定義の学年:")
for test in TestDefinition.objects.all():
    print(f"  ID{test.id}: '{test.grade_level}' (型: {type(test.grade_level)})")

print(f"\n生徒の学年 '{student.grade}' と一致するテスト:")
matching_tests = TestDefinition.objects.filter(grade_level=student.grade)
print(f"マッチング件数: {matching_tests.count()}")

# 5年生関連のテストを詳細確認
print(f"\n5年生関連のテスト:")
fifth_grade_tests = TestDefinition.objects.filter(grade_level__contains='5')
for test in fifth_grade_tests:
    print(f"  ID{test.id}: {test.grade_level} - {test.get_subject_display()} ({test.schedule.year}年{test.schedule.get_period_display()})")

# 学年の値を詳細確認
print(f"\n詳細比較:")
print(f"生徒学年: '{student.grade}' == 'elementary_5': {student.grade == 'elementary_5'}")
print(f"生徒学年: '{student.grade}' == '5': {student.grade == '5'}")

# Student modelの学年選択肢確認
from students.models import Student
print(f"\nStudent modelの学年選択肢:")
for choice in Student.GRADE_CHOICES:
    print(f"  {choice[0]}: {choice[1]}")

# TestDefinition modelの学年選択肢確認
from tests.models import TestDefinition
print(f"\nTestDefinition modelの学年選択肢:")
for choice in TestDefinition.GRADE_CHOICES:
    print(f"  {choice[0]}: {choice[1]}")
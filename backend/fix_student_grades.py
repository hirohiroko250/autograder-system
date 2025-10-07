#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'autograder.settings')
django.setup()

from students.models import Student

def fix_student_grades():
    # 学年マッピング
    grade_mapping = {
        '1': 'elementary_1',
        '2': 'elementary_2', 
        '3': 'elementary_3',
        '4': 'elementary_4',
        '5': 'elementary_5',
        '6': 'elementary_6',
        '中学1年年': 'middle_1',
        '中学2年年': 'middle_2',
        '中学3年年': 'middle_3',
    }
    
    students = Student.objects.all()
    updated_count = 0
    
    for student in students:
        old_grade = student.grade
        if old_grade in grade_mapping:
            new_grade = grade_mapping[old_grade]
            student.grade = new_grade
            student.save()
            print(f"生徒{student.student_id} ({student.name}): '{old_grade}' → '{new_grade}'")
            updated_count += 1
        else:
            print(f"生徒{student.student_id} ({student.name}): '{old_grade}' - マッピングなし")
    
    print(f"\n更新完了: {updated_count}件の生徒データを更新しました")

if __name__ == "__main__":
    fix_student_grades()
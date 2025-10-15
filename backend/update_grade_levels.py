#!/usr/bin/env python
"""
既存のTestDefinitionの学年レベルを新しい形式に更新するスクリプト
"""
import os
import sys
import django

# Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'autograder.settings')
django.setup()

from tests.models import TestDefinition

def update_grade_levels():
    """既存の学年レベルを新しい形式に更新"""
    
    # 既存データのマッピング
    grade_mapping = {
        'elementary': 'elementary_1',  # デフォルトで小学1年生にする
        'middle_school': 'middle_1',   # デフォルトで中学1年生にする
    }
    
    updated_count = 0
    
    for test in TestDefinition.objects.all():
        old_grade = test.grade_level
        if old_grade in grade_mapping:
            new_grade = grade_mapping[old_grade]
            test.grade_level = new_grade
            test.save()
            updated_count += 1
            print(f"Updated: {test} - {old_grade} -> {new_grade}")
    
    print(f"\nTotal updated: {updated_count} records")

if __name__ == '__main__':
    update_grade_levels()
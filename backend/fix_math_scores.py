#!/usr/bin/env python
import os
import sys
import django

# Django setup
sys.path.append('/Users/hirosesuzu/Desktop/an 小学生テスト/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'autograder.settings')
django.setup()

from tests.models import TestDefinition

math_tests = TestDefinition.objects.filter(
    schedule__year=2025,
    schedule__period='summer', 
    subject='math',
    is_active=True
)

for test in math_tests:
    print(f'Test {test.id}: {test.get_grade_level_display()} 算数')
    print(f'  Current max_score: {test.max_score}')
    
    groups = test.question_groups.all()
    actual_max = sum(group.max_score for group in groups)
    print(f'  Sum of question groups: {actual_max}')
    
    if test.max_score != actual_max:
        print(f'  Updating {test.max_score} to {actual_max}')
        test.max_score = actual_max
        test.save()
        print(f'  Updated')
    print()
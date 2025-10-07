#!/usr/bin/env python
import os
import django
from datetime import datetime
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'autograder.settings')
django.setup()

from test_schedules.models import TestScheduleInfo

# 現在の夏期テストの締切を確認
try:
    summer_test = TestScheduleInfo.objects.get(year='2025', period='summer')
    print(f'Current deadline: {summer_test.deadline}')
    
    # 今日の23:59:59に設定
    today = datetime.now()
    new_deadline = timezone.make_aware(datetime(today.year, today.month, today.day, 23, 59, 59))
    summer_test.deadline = new_deadline
    summer_test.save()
    
    print(f'Updated deadline: {summer_test.deadline}')
    print(f'Successfully updated to: {today.year}年{today.month}月{today.day}日 23:59')
    
except TestScheduleInfo.DoesNotExist:
    print('2025年夏期のテストスケジュールが見つかりません')
except Exception as e:
    print(f'エラーが発生しました: {e}')
#!/usr/bin/env python
import os
import django
from datetime import datetime
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'autograder.settings')
django.setup()

from test_schedules.models import TestScheduleInfo

# 夏期テストの締切を更新
summer_test = TestScheduleInfo.objects.get(year='2025', period='summer')
print(f'Current deadline: {summer_test.deadline}')

# 新しい締切日時を設定（例：8月10日 23:59:59 JST）
new_deadline = timezone.make_aware(datetime(2025, 8, 10, 23, 59, 59))
summer_test.deadline = new_deadline
summer_test.save()

print(f'Updated deadline: {summer_test.deadline}')
print('Deadline updated successfully!')
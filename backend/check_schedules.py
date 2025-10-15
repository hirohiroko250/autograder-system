#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'autograder.settings')
django.setup()

from test_schedules.models import TestScheduleInfo

print('Current test schedules:')
for ts in TestScheduleInfo.objects.all():
    print(f'{ts.year} {ts.period}: planned={ts.planned_date}, deadline={ts.deadline}')
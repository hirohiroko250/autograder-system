import os
import sys
import django

# Setup Django environment
sys.path.append('/root/autograder-system/autograder-system/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'autograder.settings')
django.setup()

from tests.models import TestSchedule

def check_and_fix_schedule():
    year = 2025
    period = 'summer'
    
    exists = TestSchedule.objects.filter(year=year, period=period).exists()
    print(f"TestSchedule for {year} {period} exists: {exists}")
    
    if not exists:
        print(f"Creating TestSchedule for {year} {period}...")
        TestSchedule.objects.create(year=year, period=period)
        print("Created successfully.")
    else:
        print("No action needed.")

if __name__ == '__main__':
    check_and_fix_schedule()

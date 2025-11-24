import os
import django
import sys

# Setup Django environment
sys.path.append('/root/autograder-system/autograder-system/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'autograder.settings')
django.setup()

from tests.models import TestSchedule
from students.models import StudentEnrollment

year = 2025
period = 'winter'

print(f"Checking data for {year} {period}...")

try:
    schedule = TestSchedule.objects.get(year=year, period=period)
    print(f"✅ TestSchedule found: {schedule}")
except TestSchedule.DoesNotExist:
    print(f"❌ TestSchedule NOT found for {year} {period}")

enrollment_count = StudentEnrollment.objects.filter(year=year, period=period).count()
print(f"Enrollment count: {enrollment_count}")

if enrollment_count == 0:
    print(f"❌ No students enrolled for {year} {period}. This will cause a 404 in export_scores_with_students.")
else:
    print(f"✅ Found {enrollment_count} enrollments.")

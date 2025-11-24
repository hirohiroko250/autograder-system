import os
import django
import sys

# Add the current directory to sys.path
sys.path.append('/root/autograder-system/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'autograder.settings')
django.setup()

from scores.models import TestResult
from django.db.models import Count

def find_data():
    # Find a test with at least 2 results
    tests = TestResult.objects.values('test').annotate(count=Count('id')).filter(count__gte=2)
    
    if not tests.exists():
        print("No tests found with multiple students.")
        return

    test_id = tests.first()['test']
    results = TestResult.objects.filter(test_id=test_id)[:2]
    
    print(f"Found test ID: {test_id}")
    print(f"Year: {results[0].test.schedule.year}")
    print(f"Period: {results[0].test.schedule.period}")
    print(f"Student 1 ID: {results[0].student.student_id}")
    print(f"Student 2 ID: {results[1].student.student_id}")

if __name__ == '__main__':
    find_data()

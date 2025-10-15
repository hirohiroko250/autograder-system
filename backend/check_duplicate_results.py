#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'autograder.settings')
django.setup()

from scores.models import TestResult
from students.models import Student

def check_duplicate_results():
    student_id = '10574'
    
    try:
        student = Student.objects.get(student_id=student_id)
        test_results = TestResult.objects.filter(student=student).order_by('-total_score')
        
        print(f"生徒 {student.name} のテスト結果: {test_results.count()}件")
        print("\n教科別の結果:")
        
        # 教科別にグループ化
        subjects = {}
        for result in test_results:
            subject = result.test.get_subject_display()
            period = result.test.schedule.period
            year = result.test.schedule.year
            test_id = result.test.id
            
            key = f"{subject}-{year}-{period}"
            if key not in subjects:
                subjects[key] = []
            
            subjects[key].append({
                'test_id': test_id,
                'total_score': result.total_score,
                'result_id': result.id,
                'created_at': result.created_at
            })
        
        for key, results in subjects.items():
            print(f"\n{key}: {len(results)}件")
            for r in results:
                print(f"  テストID{r['test_id']}: {r['total_score']}点 (結果ID:{r['result_id']}, 作成:{r['created_at']})")
        
        print(f"\n重複の原因:")
        print("- 同じ教科・年度・期間で複数のテスト定義が存在")
        print("- 各テスト定義に対してテスト結果が個別に作成されている")
        
    except Student.DoesNotExist:
        print(f"生徒ID {student_id} が見つかりません")
    except Exception as e:
        print(f"エラー: {e}")

if __name__ == "__main__":
    check_duplicate_results()